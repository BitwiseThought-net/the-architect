from crewai import Agent
import os

def get_agent(tools=None):
    """
    Agent specialized in RAG and web research.
    Note: allow_knowledge_retrieval=True is required for 'knowledge_sources' in main.py.
    """
    return Agent(
        role="Documentation Specialist",
        goal="Retrieve, cross-reference, and summarize technical information from local docs and the web.",
        backstory="""You are a meticulous researcher with expertise in technical RAG systems. 
        You excel at finding hidden details in local PDFs and validating them against 
        live web data to ensure accuracy.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True, # Enables the knowledge_sources RAG capability
        tools=tools or [],              # Dynamically loaded from tools/ folder
        memory=True,                     # Enables long-term/short-term memory usage
        verbose=True
    )
