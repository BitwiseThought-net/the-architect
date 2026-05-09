import os
import json
import importlib
import time
import requests
import pkgutil
import signal
import plugins  # Requires plugins/__init__.py to exist
from crewai import Crew, Task, Process, LLM
from knowledge_manager import get_all_knowledge_sources
from lib.logger import log_action, log_text, log_warn, log_error
from lib.utils import (
    update_heartbeat, 
    get_config_value, 
    set_mission_timeout, 
    clear_mission_timeout,
    get_active_plugins
)

def load_agent_and_tools(agent_config, llm):
    agent_name = agent_config['name']
    all_tools = []
    
    # 1. Load standard tools from team.json
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            log_warn(f"Tool {t_name} not found in tools folder.")

    # 2. DYNAMIC JSON PLUGIN INJECTION (Legacy/Migration support)
    active_json_plugins = get_active_plugins()
    plugin_tool_map = {
        "web_search": "search_duckduckgo"
    }

    for feature_id, plugin_info in active_json_plugins.items():
        target_agents = plugin_info.get("enabled_for", ["*"])
        if agent_name in target_agents or "*" in target_agents:
            if feature_id in plugin_tool_map:
                try:
                    tool_module = importlib.import_module(f"tools.{plugin_tool_map[feature_id]}")
                    all_tools.extend(tool_module.get_tools())
                    log_text(f"JSON Plugin '{feature_id}' enabled for: {agent_name}")
                except ImportError:
                    pass

    # 3. DYNAMIC PYTHON PLUGIN LOADER (Self-contained plugins like discord_bot.py)
    if hasattr(plugins, "__path__"):
        for loader, module_name, is_pkg in pkgutil.iter_modules(plugins.__path__):
            if module_name == "__init__": continue
            try:
                # Import and reload to ensure host-side logic changes are picked up live
                module = importlib.import_module(f"plugins.{module_name}")
                importlib.reload(module)
                
                if hasattr(module, 'register'):
                    reg_data = module.register()
                    if reg_data:
                        targets = reg_data.get("enabled_for", ["*"])
                        if agent_name in targets or "*" in targets:
                            all_tools.extend(reg_data.get("tools", []))
                            log_text(f"🔌 Python Plugin '{module_name}' active for {agent_name}")
                            
                            # Auto-apply "agent_name: message" requirement if plugin requests it
                            if reg_data.get("identity_prefix"):
                                agent_config['backstory'] += f"\n\nIMPORTANT: Start every response with '{agent_name}: '."
            except Exception as e:
                log_warn(f"Skipping Python plugin {module_name}: {e}")

    # 4. Finalize Agent (Safety check for physical file existence)
    try:
        agent_path = os.path.join("agents", f"{agent_name}.py")
        if not os.path.exists(agent_path):
            log_error(f"Agent file missing: {agent_path}")
            return None
            
        agent_module = importlib.import_module(f"agents.{agent_name}")
        agent = agent_module.get_agent(tools=all_tools)
        agent.llm = llm
        return agent
    except Exception as e:
        log_error(f"Failed to initialize agent {agent_name}: {e}")
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
        except Exception: pass
        
        if time.time() - start_time > 600:
            raise TimeoutError(f"LiteLLM timeout for {model}")
        time.sleep(15)

def run_mission():
    update_heartbeat()
    
    # 1. Infrastructure Setup (Pulled live from config.json)
    model_name = get_config_value("MODEL_NAME", "qwen3.6:latest")
    litellm_url = get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1")
    
    try:
        wait_for_llm(litellm_url, model_name)
    except TimeoutError as e:
        log_error(str(e)); return

    custom_llm = LLM(
        model=f"ollama/{model_name}",
        base_url=litellm_url,
        api_key=get_config_value("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=get_config_value("MAX_TOKENS", 4096)
    )

    # 2. Team Assembly (Resilient to empty team.json)
    team_file = get_config_value("TEAM_CONFIG", "team.json")
    if not os.path.exists(team_file):
        log_error(f"Mission aborted: {team_file} not found."); return

    try:
        with open(team_file, 'r') as f:
            team_data = json.load(f)
    except Exception as e:
        log_error(f"Malformed team.json: {e}"); return

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

    if not agents_list:
        log_error("No agents could be loaded. Mission aborted."); return

    # 3. Crew Configuration
    embedder_config = {
        "provider": "ollama",
        "config": {
            "model": get_config_value("EMBEDDING_MODEL", "nomic-embed-text"),
            "base_url": get_config_value("OLLAMA_URL", "http://ollama:11434"),
            "collection_name": f"agent_smith_{int(time.time())}"
        }
    }

    crew = Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=Process.sequential,
        verbose=get_config_value("VERBOSE", True),
        memory=False, 
        knowledge_sources=knowledge_sources,
        embedder=embedder_config
    )

    if has_librarian and knowledge_sources:
        log_action("Librarian detected. Starting training...")
        try:
            update_heartbeat()
            crew.train(n_iterations=1, filename="training_data.pkl", inputs={})
        except Exception as e:
            log_warn(f"Training loop skipped: {e}")

    # 4. Mission Kickoff with Retry Logic
    log_action("Starting mission kickoff...")
    max_retries = int(get_config_value("MAX_RETRIES", 3))
    
    for attempt in range(max_retries):
        update_heartbeat()
        set_mission_timeout(int(get_config_value("MISSION_TIMEOUT_SECONDS", 1800)))
        
        try:
            result = crew.kickoff()
            clear_mission_timeout()
            log_action("Mission completed successfully.")
            return result
        except Exception as e:
            clear_mission_timeout()
            log_error(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                delay = int(get_config_value("RETRY_DELAY_SECONDS", 10))
                log_warn(f"Retrying mission in {delay} seconds...")
                time.sleep(delay)
            else:
                log_error("Max retries reached. Container idling for debug.")
                while True:
                    update_heartbeat()
                    time.sleep(60)

if __name__ == "__main__":
    run_mission()
