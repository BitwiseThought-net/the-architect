from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    return Agent(
        role="Documentation Specialist",
        goal="Retrieve, cross-reference, and summarize technical information from local docs and the web.",
        backstory="""You are a meticulous researcher with expertise in technical RAG systems. 
        You excel at finding hidden details in local PDFs and validating them against 
        live web data to ensure accuracy.""",
#        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
#        llm=f"ollama/{os.getenv('MODEL_NAME')}",
        llm=local_llm,
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True, # Enables the knowledge_sources RAG capability
        tools=tools or [],              # Dynamically loaded from tools/ folder
        memory=True,                     # Enables long-term/short-term memory usage
        verbose=True
    )
