import os
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langchain_groq import ChatGroq
import config
from search_tools import unified_search

class KnowledgeBaseTool(BaseTool):
    name: str = "Knowledge Base Search Tool"
    description: str = "Searches the complete knowledge base (Quran, Hadith, Web) for information."
    quran_retriever: object
    hadith_retriever: object

    def _run(self, query: str) -> str:
        # 1. Search religious texts from Milvus
        quran_results = self.quran_retriever.invoke(query)
        hadith_results = self.hadith_retriever.invoke(query)
        
        # 2. Search the web
        web_search_output = unified_search(query)
        web_results = web_search_output.get("web_results", [])

        # 3. Format Context
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
    Creates a Failover LLM Chain (Single Object).
    """
    
    # --- LITELLM CONFIGURATION (Crucial for Azure Fix) ---
    # We map config vars to what LiteLLM expects internally
    os.environ["AZURE_API_KEY"] = config.AZURE_API_KEY
    os.environ["AZURE_API_BASE"] = config.AZURE_API_BASE
    os.environ["AZURE_API_VERSION"] = config.AZURE_API_VERSION
    
    # 1. Azure Engine
    # We pass model="azure/..." as per your reference to force proper routing
    azure_llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_CHAT_DEPLOYMENT_NAME,
        api_version=config.AZURE_API_VERSION,
        azure_endpoint=config.AZURE_API_BASE,
        api_key=config.AZURE_API_KEY,
        model=f"azure/{config.AZURE_CHAT_DEPLOYMENT_NAME}",
        temperature=0.7,
        max_retries=1
    )

    # 2. Groq Engine
    groq_llm = ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL_NAME,
        temperature=0.7,
        max_retries=1
    )

    # 3. Return based on Priority
    if config.LLM_PROVIDER == "groq":
        print(f"--- [SYSTEM] Primary: Groq | Backup: Azure ---")
        return groq_llm.with_fallbacks([azure_llm])
    else:
        print(f"--- [SYSTEM] Primary: Azure | Backup: Groq ---")
        return azure_llm.with_fallbacks([groq_llm])

def create_crew(quran_retriever, hadith_retriever):
    """
    Creates a SINGLE AGENT Crew.
    One Grandmaster agent handles Research -> Reasoning -> JSON Output.
    """
    
    knowledge_base_tool = KnowledgeBaseTool(
        quran_retriever=quran_retriever, 
        hadith_retriever=hadith_retriever
    )
    
    llm = create_hybrid_llm()

    # --- SINGLE AGENT: The Grandmaster ---
    grandmaster = Agent(
        role='Grandmaster Islamic Scholar & Tech Synthesizer',
        goal='Provide a comprehensive, accurate answer to {topic} using religious and secular sources, strictly formatted as JSON.',
        backstory='You are an elite AI Scholar capable of deep religious research and precise technical data formatting. You perform the search, analyze the data, and output the final JSON yourself.',
        tools=[knowledge_base_tool],
        llm=llm,
        verbose=True
    )
    
    # --- SINGLE TASK: Research & Format ---
    json_schema = """{
        "status": "ok" | "insufficient_data",
        "language": "en" | "id",
        "answer": "Natural, helpful reply in user's language.",
        "chain_of_thought": "Your reasoning process.",
        "sources": ["List brief quotes from Quran/Hadith found."],
        "web_sources": [{"title":"...", "url":"...", "snippet":"...", "provider":"..."}],
        "follow_up_questions": ["Question 1", "Question 2"]
    }"""

    master_task = Task(
        description=f"""
        1. RESEARCH: Use your tool to search for {topic}.
        2. ANALYZE: Review the Quran, Hadith, and Web results provided by the tool.
        3. SYNTHESIZE: Create a helpful answer based strictly on the findings.
        4. FORMAT: Output the result as a VALID JSON object matching this schema:
        {json_schema}
        
        DO NOT output markdown blocks (```json). Just the raw JSON string.
        """,
        expected_output='A valid JSON string containing the research results.',
        agent=grandmaster
    )

    return Crew(agents=[grandmaster], tasks=[master_task], process=Process.sequential, verbose=True)