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
    except Exception as e:
        log_error(f"Agent {agent_config['name']} loading failed: {e}")
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
    # We add a high context window and a lower temperature to prevent 
    # the model from getting 'confused' and returning empty strings.
    custom_llm = LLM(
        model=f"ollama/{model_name}",
        base_url="http://agent-litellm:4000/v1",
        api_key="sk-local-1234",
        temperature=0.3,      # Lower temperature = more stable formatting
        max_tokens=4096,     # Ensure enough room for 'Thoughts'
        timeout=300          # Allow 5 mins for local model generation
    )

    with open('config.json', 'r') as f:
        config = json.load(f)

    knowledge_sources = get_all_knowledge_sources()
    agents_list = []
    tasks_list = []
    has_librarian = False

    # --- STEP 3: INITIALIZE AGENTS AND TASKS ---
    for item in config.get('active_agents', []):
        agent = load_agent_and_tools(item)
        if agent:
            # FORCE the agent to use our pre-configured stable LLM
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

    # --- STEP 4: CONFIGURE CREW ---
    crew = Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=Process.sequential,
        verbose=True,
        memory=True,
        knowledge_sources=knowledge_sources
    )

    # --- STEP 5: EXECUTION ---
    # If the Librarian is present, handle the training loop carefully
    if has_librarian:
        if knowledge_sources:
            log_action("📚 Knowledge found. Synchronizing Librarian index...")
            try:
                # crew.train is sensitive; if it fails, we move to kickoff
                crew.train(n_iterations=1, filename="training_data.pkl", inputs={})
                log_text("✅ Knowledge base synchronized.")
            except Exception as e:
                log_warn(f"⚠️ Training loop skipped (LLM returned empty): {e}")
        else:
            log_text("ℹ️ Knowledge directory empty. Skipping initial index.")

    log_action("🚀 Starting mission kickoff...")
    try:
        return crew.kickoff()
    except ValueError as e:
        if "None or empty" in str(e):
            log_error("❌ Fatal Error: LLM returned an empty response. Check model context limits.")
        raise e

if __name__ == "__main__":
    run_mission()
