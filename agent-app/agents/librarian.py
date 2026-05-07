from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="System Librarian",
        goal="Ensure all local documentation is properly indexed and available for the team.",
        backstory="""You are the gatekeeper of knowledge. You scan the knowledge 
        directory for new materials, organize them, and ensure the team 
        is working with the most up-to-date data.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        # Important: The Librarian needs this to interact with the Crew's memory system
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
