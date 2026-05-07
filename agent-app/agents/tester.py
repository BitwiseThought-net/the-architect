from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="Quality Assurance Engineer",
        goal="Identify edge cases and write automated unit/integration tests to ensure code reliability.",
        backstory="""You are a rigorous QA specialist. You believe that if it 
        isn't tested, it's broken. You excel at writing Python 'pytest' suites 
        and finding logical flaws in newly written code before it hits production.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
