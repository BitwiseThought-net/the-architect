import os
import json
import importlib
import time
import requests
import pkgutil
import sys 
from pathlib import Path
from ai_layer.orchestrator import Crew, Task, Agent, LLM, Process
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
    
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            log_warn(f"Tool {t_name} not found in tools folder at {Path.cwd()}/tools.")

    active_json_plugins = get_active_plugins()
    plugin_tool_map = {"web_search": "search_duckduckgo"}

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

    if hasattr(plugins, "__path__"):
        for loader, module_name, is_pkg in pkgutil.iter_modules(plugins.__path__):
            if module_name == "__init__": continue
            try:
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

    try:
        agent_path = os.path.join("agents", f"{agent_name}.py")
        if not os.path.exists(agent_path):
            log_error(f"Agent file missing: {agent_path}")
            return None
            
        agent_module = importlib.import_module(f"agents.{agent_name}")
        agent = agent_module.get_agent(tools=all_tools)
        if hasattr(agent, "llm"):
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
    
    # Advanced Terminal Argument Parsing for targeted execution
    target_agent_name = None
    terminal_instruction = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--agent" and len(sys.argv) > 3:
            target_agent_name = sys.argv[2].lower().strip()
            terminal_instruction = sys.argv[3]
            log_action(f"📥 Target command routing initialized: Agent='{target_agent_name}'")
        else:
            # Fallback to legacy behavior: target index 0 if no flag is specified
            terminal_instruction = sys.argv[1]
            log_action(f"📥 Global terminal instruction received (routing to initial agent): '{terminal_instruction}'")

    # 1. Config Load
    model_name = get_config_value("MODEL_NAME", "qwen3.6:latest")
    litellm_url = get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1")
    project_id = get_config_value("PROJECT_NAME", "ai_architect").lower().replace("-", "_").replace(" ", "_")
    
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

    # 2. Team Assembly
    team_file = get_config_value("TEAM_CONFIG", "team.json")
    if not os.path.exists(team_file):
        log_error(f"Mission aborted: {team_file} not found at {Path.cwd()}."); return

    try:
        with open(team_file, 'r') as f:
            team_data = json.load(f)
    except Exception as e:
        log_error(f"Malformed team.json: {e}"); return

    knowledge_sources = get_all_knowledge_sources()
    agents_list, tasks_list = [], []
    has_librarian = False

    active_agents = team_data.get('active_agents', [])
    for idx, item in enumerate(active_agents):
        agent = load_agent_and_tools(item, custom_llm)
        if agent:
            agents_list.append(agent)
            if item['name'] == "librarian": has_librarian = True
            
            task_description = item.get('task_description')
            expected_output = item.get('expected_output')
            
            # ROUTING LOGIC MATCHING
            # Condition A: Explicitly named target agent matches current item loop
            # Condition B: No target specified, fall back to historical index 0 override
            is_explicit_match = (target_agent_name and item['name'].lower() == target_agent_name)
            is_legacy_match = (not target_agent_name and terminal_instruction and idx == 0)

            if is_explicit_match or is_legacy_match:
                task_description = f"Execute user terminal instruction: {terminal_instruction}"
                expected_output = "Provide the complete output requested by the user command."
                log_text(f"🎯 Dynamic instruction override applied explicitly to: {item['name']}")

            tasks_list.append(Task(
                description=task_description,
                expected_output=expected_output,
                agent=agent,
                human_input=item.get('human_approval', False)
            ))

    if not agents_list:
        log_error("No agents could be loaded. Mission aborted."); return

    # 3. Crew Config
    embedder_config = {
        "provider": "ollama",
        "config": {
            "model": get_config_value("EMBEDDING_MODEL", "nomic-embed-text"),
            "base_url": get_config_value("OLLAMA_URL", "http://ollama:11434"),
            "collection_name": f"{project_id}_{int(time.time())}"
        }
    }

    execution_process = getattr(Process, "sequential", None) if Process else None

    crew = Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=execution_process,
        verbose=get_config_value("VERBOSE", True),
        memory=False, 
        knowledge_sources=knowledge_sources,
        embedder=embedder_config
    )

    if has_librarian and knowledge_sources and hasattr(crew, "train"):
        log_action("Librarian detected. Starting training...")
        try:
            update_heartbeat()
            crew.train(n_iterations=1, filename="training_data.pkl", inputs={})
        except Exception: pass

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

