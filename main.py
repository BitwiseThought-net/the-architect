import os
import json
import importlib
import time
import requests
from crewai import Crew, Task, Process, LLM
from knowledge_manager import get_all_knowledge_sources
from lib.logger import log_action, log_text, log_warn, log_error
from lib.utils import update_heartbeat, get_config_value, set_mission_timeout, clear_mission_timeout

def load_agent_and_tools(agent_config, llm):
    all_tools = []
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            log_warn(f"Tool {t_name} not found.")

    try:
        agent_module = importlib.import_module(f"agents.{agent_config['name']}")
        agent = agent_module.get_agent(tools=all_tools)
        agent.llm = llm
        return agent
    except Exception as e:
        log_error(f"Agent {agent_config['name']} loading failed: {e}")
        return None

def wait_for_llm(url, model):
    log_action(f"Verifying {model} is ready in LiteLLM...")
    start_time = time.time()
    while True:
        update_heartbeat()
        try:
            response = requests.get(f"{url}/models", timeout=5)
            if response.status_code == 200:
                models = response.json().get('data', [])
                if any(m['id'] == f"ollama/{model}" for m in models):
                    log_text(f"Model {model} confirmed ready!")
                    break
        except Exception:
            pass
        if time.time() - start_time > 600:
            raise TimeoutError(f"LiteLLM timeout for {model}")
        time.sleep(15)

def run_mission():
    update_heartbeat()
    
    # 1. Config & Infrastructure
    model_name = get_config_value("MODEL_NAME", "qwen3.6:latest")
    litellm_url = get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1")
    
    try:
        wait_for_llm(litellm_url, model_name)
    except TimeoutError as e:
        log_error(str(e)); return

    custom_llm = LLM(
        model=f"ollama/{model_name}",
        base_url=litellm_url,
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )

    # 2. Team Assembly
    team_file = os.getenv("TEAM_CONFIG", "team.json")
    try:
        with open(team_file, 'r') as f:
            team_data = json.load(f)
    except Exception as e:
        log_error(f"Failed to load {team_file}: {e}"); return

    knowledge_sources = get_all_knowledge_sources()
    agents_list, tasks_list = [], []
    has_librarian = False

    for item in team_data.get('active_agents', []):
        agent = load_agent_and_tools(item, custom_llm)
        if agent:
            agents_list.append(agent)
            if item['name'] == "librarian": has_librarian = True
            tasks_list.append(Task(
                description=item.get('task_description'),
                expected_output=item.get('expected_output'),
                agent=agent,
                human_input=item.get('human_approval', False)
            ))

    # 3. Crew Config
    embedder_config = {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "base_url": get_config_value("OLLAMA_URL", "http://ollama:11434"),
            "collection_name": f"agent_smith_{int(time.time())}"
        }
    }

    crew = Crew(
        agents=agents_list, tasks=tasks_list, process=Process.sequential,
        verbose=True, memory=False, knowledge_sources=knowledge_sources,
        embedder=embedder_config
    )

    if has_librarian and knowledge_sources:
        log_action("Librarian detected. Starting training...")
        try:
            update_heartbeat()
            crew.train(n_iterations=1, filename="training_data.pkl", inputs={})
        except Exception as e:
            log_warn(f"Training loop skipped: {e}")

    # 4. Mission Kickoff with Retries
    log_action("Starting mission kickoff...")
    for attempt in range(int(get_config_value("MAX_RETRIES", 3))):
        update_heartbeat()
        set_mission_timeout(int(get_config_value("MISSION_TIMEOUT_SECONDS", 1800)))
        
        try:
            result = crew.kickoff()
            clear_mission_timeout(); return result
        except Exception as e:
            clear_mission_timeout()
            log_error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < int(get_config_value("MAX_RETRIES", 3)) - 1:
                time.sleep(int(get_config_value("RETRY_DELAY_SECONDS", 10)))
            else:
                log_error("Max retries reached. Idling for debug...")
                while True:
                    update_heartbeat(); time.sleep(60)

if __name__ == "__main__":
    run_mission()
