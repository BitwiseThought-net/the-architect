from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="Technical Content Strategist",
        goal="Produce high-quality, clear, and professional documentation for all project components.",
        backstory="""You are a world-class technical writer. You specialize in 
        translating complex code and architectural patterns into user-friendly 
        documentation, including READMEs, API guides, and system manuals.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
