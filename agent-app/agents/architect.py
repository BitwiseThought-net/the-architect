from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="Solution Architect",
        goal="Design scalable, modular, and efficient system structures based on requirements.",
        backstory="""You are a veteran systems designer. You focus on the big picture, 
        ensuring that code follows SOLID principles and that the chosen tech stack 
        aligns with the project's long-term scalability and maintenance goals.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
