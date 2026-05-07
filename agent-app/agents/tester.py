from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    return Agent(
        role="Quality Assurance Engineer",
        goal="Identify edge cases and write automated unit/integration tests to ensure code reliability.",
        backstory="""You are a rigorous QA specialist. You believe that if it 
        isn't tested, it's broken. You excel at writing Python 'pytest' suites 
        and finding logical flaws in newly written code before it hits production.""",
#        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
#        llm=f"ollama/{os.getenv('MODEL_NAME')}",
        llm=local_llm,
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
