import os
import json
import importlib
import time
import requests
from crewai import Crew, Task, Process, LLM
from knowledge_manager import get_all_knowledge_sources
from lib.logger import log_action, log_text, log_warn, log_error

def load_agent_and_tools(agent_config):
    all_tools = []
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            log_warn(f"Tool {t_name} not found.")

    try:
        agent_module = importlib.import_module(f"agents.{agent_config['name']}")
        return agent_module.get_agent(tools=all_tools)
    except ImportError:
        log_error(f"Agent {agent_config['name']} not found.")
        return None

def run_mission():
    # --- STEP 1: WAIT FOR MODEL READINESS ---
    model_name = os.getenv("MODEL_NAME", "qwen3.6:latest")
    log_action(f"Verifying {model_name} is fully pulled in LiteLLM...")

    start_time = time.time()
    while True:
        try:
            response = requests.get("http://agent-litellm:4000/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json().get('data', [])
                if any(m['id'] == f"ollama/{model_name}" for m in models):
                    log_text(f"Model {model_name} confirmed ready!")
                    break
        except Exception:
            pass

        if time.time() - start_time > 600:
            log_error(f"Timeout: {model_name} did not become ready in time.")
            return

        log_text(f"Still waiting for {model_name} to finish pulling...")
        time.sleep(15)

    # --- STEP 2: DEFINE STABLE LLM ---
    custom_llm = LLM(
        model=f"ollama/{model_name}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    with open('config.json', 'r') as f:
        config = json.load(f)

    knowledge_sources = get_all_knowledge_sources()
    agents_list = []
    tasks_list = []
    has_librarian = False

    for item in config.get('active_agents', []):
        agent = load_agent_and_tools(item)
        if agent:
            agent.llm = custom_llm
            agents_list.append(agent)
            if item['name'] == "librarian":
                has_librarian = True

            tasks_list.append(Task(
                description=item.get('task_description'),
                expected_output=item.get('expected_output'),
                agent=agent,
                human_input=item.get('human_approval', False)
            ))

    crew = Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=Process.sequential,
        verbose=True,
        memory=True,
        knowledge_sources=knowledge_sources
    )

    if has_librarian:
        log_action("Librarian detected. Starting training...")
        try:
            crew.train(n_iterations=1, filename="training_data.pkl", inputs={})
            log_text("Knowledge base synchronized via training.")
        except Exception as e:
            log_warn(f"Training loop skipped: {e}. Proceeding to kickoff.")

    log_action("Starting mission kickoff...")
    return crew.kickoff()

if __name__ == "__main__":
    run_mission()
