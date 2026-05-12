import os
import json
import importlib
import time
import requests
import pkgutil
import sys
from pathlib import Path
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
    """
    Dynamically boot-straps an individual agent using its specifically defined
    framework engine while compiling its custom tool and plugin arrays.
    """
    agent_name = agent_config['name']

    # RESOLUTION PRIORITY: agent local framework > config.json global framework > default fallback
    framework = agent_config.get("framework", get_config_value("AI_FRAMEWORK", "crewai")).lower()
    log_text(f"Initializing agent '{agent_name}' using framework: [{framework}]")

    # Dynamically resolve the abstract orchestrator factory for this specific agent's target framework
    try:
        _layer = importlib.import_module(f"ai_layer.{framework}")
    except ImportError:
        log_warn(f"Factory for '{framework}' not found. Falling back to crewai engine wrapper.")
        _layer = importlib.import_module("ai_layer.crewai")

    all_tools = []

    # 1. Load standard tools from team.json mapped to the custom framework factory
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            log_warn(f"Tool {t_name} not found in tools folder.")

    # 2. DYNAMIC PYTHON PLUGIN LOADER
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if os.path.exists(plugins_dir):
        try:
            import plugins
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

                                    if reg_data.get("identity_prefix"):
                                        agent_config['backstory'] += f"\n\nIMPORTANT: Start every response with '{agent_name}: '."
                    except Exception as e:
                        log_warn(f"Skipping Python plugin {module_name}: {e}")
        except ImportError:
            pass

    # 3. Finalize Agent using the resolved local layer primitives
    try:
        agent_path = os.path.join("agents", f"{agent_name}.py")
        if not os.path.exists(agent_path):
            log_error(f"Agent file missing: {agent_path}")
            return None, None

        agent_module = importlib.import_module(f"agents.{agent_name}")

        # Build the native LLM wrapper through the specific isolated framework factory block
        native_llm = _layer.LLM(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"]
        )

        # Instantiate the explicit abstract agent class layout from the factory
        agent = _layer.Agent(
            role=agent_config.get("role", agent_name),
            goal=agent_config.get("task_description", "Execute mission assignments"),
            backstory=agent_config.get("backstory", f"Expert {agent_name} operative."),
            llm=native_llm,
            tools=all_tools
        )
        return agent, _layer
    except Exception as e:
        log_error(f"Failed to initialize multi-framework agent {agent_name}: {e}")
        return None, None

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
    global llm_config
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
            terminal_instruction = sys.argv[1]
            log_action(f"📥 Global terminal instruction received (routing to initial agent): '{terminal_instruction}'")

    # 1. Config Pull & Global Parameter Compiling
    model_name = get_config_value("MODEL_NAME", "qwen3.6:latest")
    litellm_url = get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1")
    project_id = get_config_value("PROJECT_NAME", "ai_architect").lower().replace("-", "_").replace(" ", "_")

    try:
        wait_for_llm(litellm_url, model_name)
    except TimeoutError as e:
        log_error(str(e)); return

    # Hydrate intermediate configuration dict mapping parameter values to factories
    llm_config = {
        "model": f"ollama/{model_name}",
        "base_url": litellm_url,
        "api_key": get_config_value("OPENAI_API_KEY", "sk-local-1234"),
        "temperature": float(get_config_value("TEMPERATURE", 0.3)),
        "max_tokens": get_config_value("MAX_TOKENS", 4096)
    }

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

    # Latch variable tracking the layer factory configuration of the final execution step
    master_layer = None

    active_agents = team_data.get('active_agents', [])
    for idx, item in enumerate(active_agents):
        agent, current_layer = load_agent_and_tools(item, None)
        if agent:
            agents_list.append(agent)
            master_layer = current_layer # Latches to final compiled step execution engine module

            task_description = item.get('task_description')
            expected_output = item.get('expected_output')

            is_explicit_match = (target_agent_name and item['name'].lower() == target_agent_name)
            is_legacy_match = (not target_agent_name and terminal_instruction and idx == 0)

            if is_explicit_match or is_legacy_match:
                task_description = f"Execute user terminal instruction: {terminal_instruction}"
                expected_output = "Provide complete terminal request output summary package."
                log_text(f"🎯 Dynamic instruction override applied explicitly to: {item['name']}")

            # Build the custom abstract Task class wrapper inside the respective local module layer
            task_instance = current_layer.Task(
                description=task_description,
                expected_output=expected_output,
                agent=agent
            )
            tasks_list.append(task_instance)

    if not agents_list:
        log_error("No agents could be loaded. Mission aborted."); return

    # 3. Hybrid Crew Setup & Final Handoff Compilation
    # The final master orchestration manager coordinates multi-framework string handoffs sequentially
    crew = master_layer.Crew(
        agents=agents_list,
        tasks=tasks_list,
        verbose=get_config_value("VERBOSE", True)
    )

    # 4. Hybrid Mission Kickoff with Retry Logic
    log_action("Starting hybrid multi-framework mission kickoff...")
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

