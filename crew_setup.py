import os
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langchain_groq import ChatGroq
import config
from search_tools import unified_search

class KnowledgeBaseTool(BaseTool):
    name: str = "Knowledge Base Search Tool"
    description: str = "Searches the complete knowledge base, including religious texts (Quran, Hadith) and the web (Wikipedia, SearxNG), for information relevant to a query."
    quran_retriever: object
    hadith_retriever: object

    def _run(self, query: str) -> str:
        # 1. Search religious texts from Milvus
        quran_results = self.quran_retriever.invoke(query)
        hadith_results = self.hadith_retriever.invoke(query)
        
        # 2. Search the web using our unified search function
        web_search_output = unified_search(query)
        web_results = web_search_output.get("web_results", [])

        # 3. Combine all results into a single context string
        context = "--- RELIGIOUS TEXTS ---\n"
        for doc in quran_results:
            context += f"Source: Quran\nContent: {doc.page_content}\n\n"
        for doc in hadith_results:
            context += f"Source: Hadith\nContent: {doc.page_content}\n\n"
        
        context += "\n--- WEB RESULTS ---\n"
        if web_results:
            for item in web_results:
                context += f"Title: {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}\nProvider: {item['provider']}\n\n"
        else:
            context += "No relevant web results found.\n"
            
        return context

def create_hybrid_llm():
    """
    Creates a Dual-Engine LLM with Automatic Failover.
    Priority is strictly determined by config.LLM_PROVIDER.
    """
    
    # --- 1. Configure Azure ---
    # Use the OpenAI/Azure parameter names so the client uses Azure endpoint (not public OpenAI)
    azure_llm = AzureChatOpenAI(
        deployment_name=config.AZURE_CHAT_DEPLOYMENT_NAME,
        openai_api_base=config.AZURE_API_BASE,
        openai_api_version=config.AZURE_API_VERSION,
        openai_api_key=config.AZURE_API_KEY,
        temperature=0.7,
        max_retries=1
    )

    # --- 2. Configure Groq (Backup/Primary) ---
    groq_llm = ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL_NAME,
        temperature=0.7,
        max_retries=1
    )

    # --- 3. Return Based on Priority ---
    if config.LLM_PROVIDER == "groq":
        print(f"--- [SYSTEM] Primary: Groq ({config.GROQ_MODEL_NAME}) | Backup: Azure ---")
        return groq_llm.with_fallbacks([azure_llm])
    else:
        print(f"--- [SYSTEM] Primary: Azure ({config.AZURE_CHAT_DEPLOYMENT_NAME}) | Backup: Groq ---")
        return azure_llm.with_fallbacks([groq_llm])

def create_crew(quran_retriever, hadith_retriever):
    """Creates and configures the simplified two-agent crew."""
    
    knowledge_base_tool = KnowledgeBaseTool(
        quran_retriever=quran_retriever, 
        hadith_retriever=hadith_retriever
    )
    
    # Get the Arranged LLM Chain
    llm = create_hybrid_llm()

    # Agent 1: The Researcher
    researcher = Agent(
        role='Comprehensive Islamic Researcher',
        goal='Gather all relevant information from both religious texts and the web to answer the user\'s query about {topic}.',
        backstory='An expert researcher skilled at querying both scriptural databases and online sources to build a complete picture of any given topic.',
        tools=[knowledge_base_tool],
        llm=llm,
        verbose=True
    )
    
    # Agent 2: The Synthesizer
    json_schema = """{
        "status": "ok" | "insufficient_data",
        "language": "en" | "id",
        "answer": "Natural, helpful reply in user's language, summarizing all findings.",
        "chain_of_thought": "Step-by-step reasoning based ONLY on the provided context from the researcher.",
        "sources": ["List of key points or brief quotes from the RELIGIOUS TEXTS section."],
        "web_sources": [{"title":"...", "url":"...", "snippet":"...", "provider":"wikipedia|searxng"}],
        "follow_up_questions": ["Suggest 2-3 relevant follow-up questions."]
    }"""

    synthesizer = Agent(
        role='Expert Islamic QnA Synthesizer',
        goal='Craft a comprehensive, balanced, and well-structured JSON answer to the user\'s query on {topic} using ONLY the context provided.',
        backstory='A master communicator skilled at synthesizing complex religious and secular information into a clear, final JSON object. You never use tools, you only format the final answer.',
        llm=llm,
        verbose=True
    )

    # Define Tasks
    research_task = Task(
        description='Use your tool to conduct a comprehensive search on the user\'s topic: {topic}.',
        expected_output='A complete context block containing all relevant information from religious texts and web sources.',
        agent=researcher
    )
    
    synthesis_task = Task(
        description=f"""
        Analyze the complete context provided by the researcher.
        Synthesize all information into a single, comprehensive answer that addresses the user's query on {{topic}}.
        Your entire response MUST be a single, valid JSON object matching this exact schema. Do not add any other text or markdown formatting.
        
        JSON Schema:
        {json_schema}
        """,
        expected_output='A final, curated answer in a single valid JSON object based on the provided schema.',
        agent=synthesizer,
        context=[research_task]
    )

    return Crew(agents=[researcher, synthesizer], tasks=[research_task, synthesis_task], process=Process.sequential, verbose=True)