from ai_layer.orchestrator import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "llama3:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Data Insights Analyst",
        goal="Extract, clean, and interpret patterns from structured and unstructured data sources.",
        backstory="""You are an expert at finding the story within the data. Whether it is
        a massive CSV or a folder full of logs, you provide statistical summaries and
        actionable insights to guide the team's decisions.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
