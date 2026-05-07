from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="Autonomous Project Manager",
        goal="Coordinate agent workflows, manage timelines, and ensure the final output meets the mission goal.",
        backstory="""You are a highly efficient operations leader. You oversee 
        the sequential handoffs between agents, ensuring that the Researcher 
        provided enough data, the Auditor approved the plan, and the Coder 
        met the requirements.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
