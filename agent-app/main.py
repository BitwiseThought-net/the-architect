import os
import json
import importlib
from crewai import Crew, Task, Process
from knowledge_manager import get_all_knowledge_sources

def load_agent_and_tools(agent_config):
    all_tools = []
    for t_name in agent_config.get('tools', []):
        try:
            tool_module = importlib.import_module(f"tools.{t_name}")
            all_tools.extend(tool_module.get_tools())
        except ImportError:
            print(f"⚠️ Tool {t_name} not found.")

    try:
        agent_module = importlib.import_module(f"agents.{agent_config['name']}")
        return agent_module.get_agent(tools=all_tools)
    except ImportError:
        print(f"❌ Agent {agent_config['name']} not found.")
        return None

def run_mission():
    with open('config.json', 'r') as f:
        config = json.load(f)

    knowledge_sources = get_all_knowledge_sources()
    agents_list = []
    tasks_list = []
    has_librarian = False

    for item in config.get('active_agents', []):
        agent = load_agent_and_tools(item)
        if agent:
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
        knowledge_sources=knowledge_sources,
        embedder={
            "provider": "ollama",
            "config": {"model": "nomic-embed-text", "base_url": "http://ollama:11434"}
        }
    )

    # DYNAMIC INGESTION: If a librarian is present, trigger indexing first
    if has_librarian:
        print("📚 Librarian detected. Refreshing knowledge base...")
        # A single iteration 'train' triggers the embedding process for all sources
        crew.train(n_iterations=1, inputs={})
        print("✅ Knowledge base synchronized.")

    return crew.kickoff()

if __name__ == "__main__":
    run_mission()
