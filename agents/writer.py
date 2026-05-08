from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    return Agent(
        role="Technical Content Strategist",
        goal="Produce high-quality, clear, and professional documentation for all project components.",
        backstory="""You are a world-class technical writer. You specialize in translating 
        complex code and architectural patterns into user-friendly documentation, 
        including READMEs, API guides, and system manuals.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
