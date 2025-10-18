import os
import json
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_openai import AzureChatOpenAI
from langchain_groq import ChatGroq
import config
from search_tools import unified_search

# 1. Tool Definition (LangChain Style)
class ResearchTools:
    def __init__(self, quran_retriever, hadith_retriever):
        self.quran = quran_retriever
        self.hadith = hadith_retriever

    def research(self, query: str) -> str:
        """
        Searches the Quran, Hadith, and Web for information.
        """
        # 1. Vector Search
        quran_docs = self.quran.invoke(query)
        hadith_docs = self.hadith.invoke(query)
        
        # 2. Web Search
        web_data = unified_search(query)
        web_results = web_data.get("web_results", [])

        # 3. Format Output
        context = "RELIGIOUS TEXTS\n"
        for doc in quran_docs:
            context += f"Source: Quran\nContent: {doc.page_content}\n\n"
        for doc in hadith_docs:
            context += f"Source: Hadith\nContent: {doc.page_content}\n\n"
        
        context += "\nWEB RESULTS\n"
        if web_results:
            for item in web_results:
                context += f"Title: {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}\nProvider: {item['provider']}\n\n"
        else:
            context += "No relevant web results found.\n"
            
        return context

# 2. Compatibility Wrapper
class MockCrewOutput:
    """Mimics the CrewAI output object so app.py doesn't break."""
    def __init__(self, raw_output):
        # Ensure we just get the string content
        if isinstance(raw_output, str):
            self.raw = raw_output
        else:
            self.raw = json.dumps(raw_output)

class CrewWrapper:
    """Replaces the CrewAI 'Crew' class with a LangChain AgentExecutor."""
    def __init__(self, agent_executor):
        self.executor = agent_executor

    def kickoff(self, inputs):
        topic = inputs.get('topic')
        print(f"[LangChain] Kicking off Agent for topic: {topic}")
        try:
            # Run the agent
            result = self.executor.invoke({"input": topic})
            output_str = result['output']
            
            # Cleaning: Remove markdown code blocks if the LLM added them
            output_str = output_str.replace("```json", "").replace("```", "").strip()
            
            return MockCrewOutput(output_str)
        except Exception as e:
            print(f"Agent Execution Error: {e}")
            # Return a fallback JSON error so the UI handles it gracefully
            error_json = json.dumps({
                "status": "error",
                "answer": "I encountered an error while processing your request. Please try again.",
                "chain_of_thought": str(e)
            })
            return MockCrewOutput(error_json)

# 3. LLM Factory
def create_hybrid_llm():
    # 1. Azure Setup
    azure_llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_CHAT_DEPLOYMENT_NAME,
        api_version=config.AZURE_API_VERSION,
        azure_endpoint=config.AZURE_API_BASE,
        api_key=config.AZURE_API_KEY,
        temperature=0.7,
        max_retries=1
    )

    # 2. Groq Setup
    groq_llm = ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL_NAME,
        temperature=0.7,
        max_retries=1
    )

    # 3. Priority Logic
    if config.LLM_PROVIDER == "groq":
        print(f"[SYSTEM] Primary: Groq ({config.GROQ_MODEL_NAME}) | Backup: Azure")
        return groq_llm.with_fallbacks([azure_llm])
    else:
        print(f"[SYSTEM] Primary: Azure ({config.AZURE_CHAT_DEPLOYMENT_NAME}) | Backup: Groq")
        return azure_llm.with_fallbacks([groq_llm])

# 4. Main Creation Function
def create_crew(quran_retriever, hadith_retriever):
    # Initialize Tools
    research_tools = ResearchTools(quran_retriever, hadith_retriever)
    
    # Define the Tool for the Agent
    tools = [
        Tool(
            name="Knowledge_Base_Search",
            func=research_tools.research,
            description="Useful for searching the Quran, Hadith, and the Web. Input should be the search topic."
        )
    ]

    # Get LLM
    llm = create_hybrid_llm()

    # Define the Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the 'Grandmaster Islamic Scholar', a specialized AI.
        
        YOUR GOAL: Provide a comprehensive, accurate answer to the user's query using the 'Knowledge_Base_Search' tool.
        
        CRITICAL RULES:
        1. You MUST use the 'Knowledge_Base_Search' tool to gather information.
        2. You MUST output ONLY a valid JSON string. Do not output any thinking text outside the JSON.
        3. Do not use Markdown formatting (like ```json).
        
        JSON SCHEMA:
        {{
            "status": "ok",
            "language": "en" | "id",
            "answer": "A helpful, natural language answer based on the search results.",
            "chain_of_thought": "Brief explanation of your reasoning.",
            "sources": ["List brief quotes/citations from Quran/Hadith found."],
            "web_sources": [{{"title": "...", "url": "...", "snippet": "...", "provider": "..."}}],
            "follow_up_questions": ["Question 1", "Question 2"]
        }}
        """),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Create the Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create the Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Return the Wrapper (compatible with app.py)
    return CrewWrapper(agent_executor)