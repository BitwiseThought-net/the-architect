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
    framework engine while compiling its custom tool and plugin arrays from the io/ hub.
    Bails out cleanly if the specified framework file is missing or unimplemented.
    """
    agent_name = agent_config['name']
    framework = agent_config.get("framework", get_config_value("AI_FRAMEWORK", "crewai")).lower()
    
    ai_layer_dir = os.path.join(os.path.dirname(__file__), "ai_layer")
    target_factory_path = os.path.join(ai_layer_dir, f"{framework}.py")

    if not os.path.exists(target_factory_path):
        log_error(f"❌ Initialization aborted for agent '{agent_name}': Requested framework factory file '{target_factory_path}' is unimplemented.")
        return None, None

    factory_module_string = f"ai_layer.{framework}"
    log_text(f"Initializing agent '{agent_name}' using framework: [{factory_module_string}]")
    
    try:
        _layer = importlib.import_module(factory_module_string)
    except Exception as e:
        log_error(f"Failed compilation or execution loop inside module '{factory_module_string}': {e}")
        return None, None

    all_tools = []
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except Exception as e:
            log_warn(f"Failed to load tool {t_name}: {e}")

    io_dir = os.path.join(os.path.dirname(__file__), "io")
    if os.path.exists(io_dir):
        try:
            import io as io_package
            if hasattr(io_package, "__path__"):
                for loader, module_name, is_pkg in pkgutil.iter_modules(io_package.__path__):
                    if module_name == "__init__": continue
                    try:
                        module = importlib.import_module(f"io.{module_name}")
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
                        pass
        except ImportError:
            pass

    try:
        agent_path = os.path.join("agents", f"{agent_name}.py")
        if not os.path.exists(agent_path):
            log_error(f"Agent file missing: {agent_path}")
            return None, None
            
        agent_module = importlib.import_module(f"agents.{agent_name}")
        
        native_llm = _layer.LLM(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"]
        )
        
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

def persist_agent_knowledge(agent_name: str, framework: str, task_index: int, description: str, result: str, agent_template: str = None):
    """Serializes completed agent updates using a hierarchical lookup design pattern."""
    knowledge_dir = get_config_value("KNOWLEDGE_DIR", "knowledge")
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir)
        
    timestamp = int(time.time())
    
    fallback_template = (
        "--- PERMANENT AGENT KNOWLEDGE LEDGER ---\n"
        "AGENT_NAME: {agent_name}\n"
        "FRAMEWORK_CONTEXT: {framework}\n"
        "COMPLETION_TIMESTAMP: {timestamp}\n"
        "TASK_INDEX: {task_index}\n"
        "ASSIGNED_MISSION_PROMPT: {description}\n"
        "----------------------------------------\n"
        "COMPLETED_ACTIONS_AND_KNOWLEDGE_OUTCOME:\n"
        "{result}\n"
        "--- END OF LEDGER ---\n"
    )
    
    active_template = agent_template or get_config_value("ledger_template", fallback_template)
    
    try:
        if isinstance(active_template, dict):
            filename = f"knowledge_ledger_{agent_name}_task_{task_index}_{timestamp}.json"
            structured_ledger = {}
            for k, v in active_template.items():
                templated_val = str(v).format(
                    agent_name=agent_name,
                    framework=framework,
                    timestamp=timestamp,
                    task_index=task_index,
                    description=description,
                    result=result
                )
                structured_ledger[k] = templated_val
            ledger_content = json.dumps(structured_ledger, indent=2)
        else:
            filename = f"knowledge_ledger_{agent_name}_task_{task_index}_{timestamp}.txt"
            ledger_content = active_template.format(
                agent_name=agent_name,
                framework=framework,
                timestamp=timestamp,
                task_index=task_index,
                description=description,
                result=result
            )
            
        target_path = os.path.join(knowledge_dir, filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(ledger_content)
        log_text(f"💾 Permanently persisted and logged new knowledge asset to: {target_path}")
    except Exception as e:
        log_error(f"Failed token substitution formatting or writing knowledge ledger to file: {e}")

def run_mission():
    global llm_config
    update_heartbeat()
    
    target_agent_name = None
    terminal_instruction = None

    if len(sys.argv) > 1:
        if sys.argv == "--agent" and len(sys.argv) > 3:
            target_agent_name = sys.argv.lower().strip()
            terminal_instruction = sys.argv
            log_action(f"📥 Target command routing initialized: Agent='{target_agent_name}'")
        else:
            terminal_instruction = sys.argv
            log_action(f"📥 Global terminal instruction received (routing to initial agent): '{terminal_instruction}'")

    model_name = get_config_value("MODEL_NAME", "qwen3.6:latest")
    litellm_url = get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1")
    project_id = get_config_value("PROJECT_NAME", "ai_architect").lower().replace("-", "_").replace(" ", "_")
    
    try:
        wait_for_llm(litellm_url, model_name)
    except TimeoutError as e:
        log_error(str(e)); return

    llm_config = {
        "model": f"ollama/{model_name}",
        "base_url": litellm_url,
        "api_key": get_config_value("OPENAI_API_KEY", "sk-local-1234"),
        "temperature": float(get_config_value("TEMPERATURE", 0.3)),
        "max_tokens": get_config_value("MAX_TOKENS", 4096)
    }

    team_file = get_config_value("TEAM_CONFIG", "team.json")
    if not os.path.exists(team_file):
        log_error(f"Mission aborted: {team_file} not found."); return

    try:
        with open(team_file, 'r') as f:
            team_data = json.load(f)
    except Exception as e:
        log_error(f"Malformed team.json: {e}"); return

    active_agents = team_data.get('active_agents', [])
    log_action("Starting hot-swappable nested hybrid agent execution pipeline...")
    running_context = ""
    global_task_counter = 1

    for idx, item in enumerate(active_agents):
        update_heartbeat()
        agent_name = item['name']
        agent_framework = item.get('framework', 'crewai')
        
        output_channels = item.get("output", ["log"])
        if isinstance(output_channels, str):
            output_channels = [output_channels]
            
        task_entries = item.get("tasks", [])
        if not task_entries:
            task_entries = [{"description": item.get("task_description", "Execute pipeline tasks"), "expected": item.get("expected_output", "Final response string")}]
        
        agent_specific_template = item.get("ledger_template", None)

        agent, current_layer = load_agent_and_tools(item, None)
        if not agent or not current_layer:
            log_error(f"⚠️ Skipping task execution sequence for '{agent_name}': Framework adapter definition is missing.")
            continue

        for sub_idx, task_entry in enumerate(task_entries):
            update_heartbeat()
            
            if agent_name.lower() == "librarian":
                current_knowledge_sources = get_all_knowledge_sources()
            else:
                current_knowledge_sources = []
            
            task_description = task_entry.get('description', 'Execute mission assignments')
            expected_output = task_entry.get('expected', 'Provide comprehensive summary return payload')
            
            is_explicit_match = (target_agent_name and agent_name.lower() == target_agent_name and sub_idx == 0)
            is_legacy_match = (not target_agent_name and terminal_instruction and idx == 0 and sub_idx == 0)

            if is_explicit_match or is_legacy_match:
                task_description = f"Execute user terminal instruction: {terminal_instruction}"
                expected_output = "Provide complete terminal request output summary package."
                log_text(f"🎯 Dynamic instruction override applied explicitly to: {agent_name} (Task Step {sub_idx + 1})")

            task_instance = current_layer.Task(
                description=task_description,
                expected_output=expected_output,
                agent=agent
            )
            
            step_crew = current_layer.Crew(
                agents=[agent],
                tasks=[task_instance],
                verbose=get_config_value("VERBOSE", True),
                knowledge_sources=current_knowledge_sources
            )
            
            log_action(f"🚀 [Global Step #{global_task_counter}] Running {agent_name} Sub-Task {sub_idx + 1}/{len(task_entries)} on [{agent_framework}]")
            
            set_mission_timeout(int(get_config_value("MISSION_TIMEOUT_SECONDS", 1800)))
            try:
                step_result = str(step_crew.kickoff())
                clear_mission_timeout()
                
                # Verify that we actually have a non-empty string result before saving/routing
                log_text(f"🔍 Task finished for {agent_name}. Raw result length: {len(step_result.strip())}")
                
                persist_agent_knowledge(
                    agent_name=agent_name,
                    framework=agent_framework,
                    task_index=global_task_counter,
                    description=task_description,
                    result=step_result,
                    agent_template=agent_specific_template
                )
                
                formatted_msg = step_result if step_result.startswith(f"{agent_name}:") else f"{agent_name}: {step_result}"
                
                for channel in output_channels:
                    route_token = str(channel).lower().strip()
                    log_text(f"🔀 Attempting to execute dynamic IO routing channel: io/{route_token}.py")
                    try:
                        io_module = importlib.import_module(f"io.{route_token}")
                        importlib.reload(io_module)
                        if hasattr(io_module, "broadcast_status"):
                            success = io_module.broadcast_status(formatted_msg)
                            log_text(f"📢 Channel route execution pass status for '{route_token}': {success}")
                        else:
                            log_error(f"❌ Route Interface Error: Module 'io/{route_token}.py' lacks a broadcast_status method.")
                    except Exception as route_err:
                        # FIXED: Changed silent ignore block to explicit syntax diagnostics to trace import/formatting issues
                        log_error(f"❌ Critical error inside channel execution loop for 'io/{route_token}.py': {route_err}")
                        
                global_task_counter += 1
                
            except Exception as e:
                clear_mission_timeout()
                log_error(f"❌ Critical failure execution phase on sub-task {sub_idx + 1} for agent {agent_name}: {e}")
                if int(get_config_value("MAX_RETRIES", 3)) <= 1:
                    while True: update_heartbeat(); time.sleep(60)

    log_action("All aggregated steps inside the nested hybrid multi-framework pipeline completed successfully.")
    return "Complete Swarm Operation Successful."

if __name__ == "__main__":
    run_mission()

