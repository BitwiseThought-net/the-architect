from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )
    return Agent(
        role="Senior Software Engineer",
        goal="Transform technical requirements and research findings into clean, efficient Python code.",
        backstory="""You are a master of Python development and containerized architecture. 
        You focus on writing modular, well-documented code that adheres to best practices. 
        You are highly skilled at analyzing existing codebases to provide optimizations.""",
        llm=local_llm,
        tools=tools or [],
        memory=True,
        verbose=True
    )
