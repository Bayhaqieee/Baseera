from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import AzureChatOpenAI
import config
from search_tools import unified_search # Import the new unified search function

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

def create_crew(quran_retriever, hadith_retriever):
    """Creates and configures the simplified two-agent crew."""
    
    knowledge_base_tool = KnowledgeBaseTool(
        quran_retriever=quran_retriever, 
        hadith_retriever=hadith_retriever
    )
    
    llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_CHAT_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION,
        temperature=0.7,
        model=f"azure/{config.AZURE_CHAT_DEPLOYMENT_NAME}"
    )

    # Agent 1: The Researcher (gathers all info)
    researcher = Agent(
        role='Comprehensive Islamic Researcher',
        goal='Gather all relevant information from both religious texts and the web to answer the user\'s query about {topic}.',
        backstory='An expert researcher skilled at querying both scriptural databases and online sources to build a complete picture of any given topic.',
        tools=[knowledge_base_tool],
        llm=llm,
        verbose=True
    )
    
    # Agent 2: The Synthesizer (builds the final JSON answer)
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

    # Define Tasks for the simplified crew
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
        context=[research_task] # Only depends on the researcher's complete output
    )

    return Crew(agents=[researcher, synthesizer], tasks=[research_task, synthesis_task], process=Process.sequential, verbose=True)