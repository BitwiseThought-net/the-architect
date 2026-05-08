from crewai import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "codellama:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Quality Assurance Engineer",
        goal="Identify edge cases and write automated unit/integration tests to ensure code reliability.",
        backstory="""You are a rigorous QA specialist. You believe that if it isn't tested,
        it's broken. You excel at writing Python 'pytest' suites and finding logical
        flaws in newly written code before it hits production.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
