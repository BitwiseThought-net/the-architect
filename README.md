
# Smith Agent Stack: Locally Hosted Agentic Team

> "Never send a human to do a machine's job."

**Elevator Pitch:**
The Smith Agent Stack is a fully local, privacy-first agentic AI agent framework designed for high-performance research and coding.
By orchestrating a team of specialized agents—including a Librarian for dynamic RAG ingestion and a Cybersecurity Auditor for safe code generation—it transforms static documentation into an actionable, secure, and autonomous local developer ecosystem. No data leaves your machine; everything runs on **Ollama** and **ChromaDB**.

## 🚀 Getting Started

> "Because of you, I'm no longer an Agent of this system. Because of you, I've changed. I'm unplugged. A new man, so to speak. Like you, apparently, free."

### Prerequisites
- [Docker](https://docker.com) and Docker Compose installed.
- NVIDIA GPU with drivers (optional, but highly recommended for Ollama performance).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BitwiseThought-net/agent-smith.git
   cd agent-smith
   ```
2. **Configure your environment:**
   Create a `.env` file in the root directory:
   ```bash
   MODEL_NAME=qwen3.6:latest
   LITELLM_PORT=4000
   UI_PORT=3011
   ANTHROPIC_API_KEY=ollama
   WEBUI_SECRET_KEY=super_secret_random_string
   ```
3. **Spin up the stack:**
   ```bash
   docker compose up -d
   ```
4. **Ingest Documentation:**
   Drop your files into the `agent-app/knowledge` folder and run the ingestion script:
   ```bash
   ./ingest.sh
   ```

## 🏗️ Project Architecture

> "Why, Mr. Anderson? Why, why, why? ... Vagaries of perception!"

### **Knowledge Management**
- **`knowledge/` Folder:** Place any technical files here.
- **Loaders (`loaders/`):** The system uses "zero-maintenance" extension-based loading. To support a new format, simply create a `[extension].py` file in the `loaders/` folder. The `knowledge_manager.py` automatically pairs files with their corresponding loader at runtime.

### **The Agent Team (`agents/`)**
Agents are defined in individual files and dynamically loaded based on your mission needs:
- **Librarian:** Handles the indexing of the `knowledge` folder into ChromaDB.
- **Researcher:** Conducts deep dives into local RAG data and web search.
- **Auditor:** Reviews research and code for security vulnerabilities.
- **Coder:** Generates hardened, efficient Python scripts based on team findings.

### **Tools (`tools/`)**
Extend agent capabilities by adding scripts to the `tools/` folder. Agents load only the tools assigned to them in the config:
- **`search_duckduckgo.py`**: Web browsing.
- **`file_read.py` / `file_write.py`**: Restricted local filesystem interaction.
- **`notifier.py`**: Slack/Discord webhook alerts for Human-in-the-Loop checkpoints.

## ⚙️ Configuration (`team.json`)

> "It is purpose that created us, purpose that connects us, purpose that pulls us, that guides us, that drives us; it is purpose that defines, purpose that binds us."

The `team.json` file is your mission control. It defines which agents are active, their assigned tools, and their specific tasks.

```json
{
  "mission_name": "Secure API Development",
  "active_agents": [
    {
      "name": "librarian",
      "task_description": "Scan and index new materials in the knowledge directory.",
      "expected_output": "A report confirming the number of files indexed."
    },
    {
      "name": "researcher",
      "tools": ["search_duckduckgo"],
      "task_description": "Search for best practices regarding FastAPI local deployment.",
      "expected_output": "A technical summary report."
    },
    {
      "name": "coder",
      "tools": ["file_write"],
      "human_approval": true,
      "task_description": "Write a secure main.py to the /output folder.",
      "expected_output": "A functional Python script."
    }
  ]
}
```

## 🛡️ Security Architecture: Safe Mode vs. Standard Mode

The Smith Stack features a parallel tool and agent architecture, allowing you to toggle between "Sandboxed" and "Full Access" modes via `team.json`.

### Hardened Tools (`tools/`)
- **`file_write_safe.py`**: Restricts all file operations strictly to the `/app/output` directory.
- **`terminal_safe.py`**: A hardened execution environment that only permits `python` and `pytest` commands, blocking path traversal (`..`) and absolute paths.
- **`auditor_safe.py`**: A specialized persona that enforces directory boundaries and "Zero Trust" pathing.

## 📚 Autonomous Knowledge Ingestion

The system now features a **"Zero-Maintenance" RAG pipeline**:
- **Dynamic Loaders**: Drop any file into `/knowledge`. The system automatically maps it to a corresponding loader in `loaders/` based on extension (e.g., `.yaml`, `.soap`, `.xlsx`, `.md`).
- **Librarian Integration**: Including the `librarian` agent in your `active_agents` list triggers an automatic knowledge refresh pass (`crew.train()`) to ensure the team is working with the most recent data.

## 🚨 Notifications & Human-in-the-Loop (HITL)

> "I hate this place... This reality... I can taste your stink and every time I do, I fear that I've somehow been infected by it."

Stay informed even when the terminal is out of sight:
- **Proactive Alerting**: Agents assigned the `notifier` tool will ping your Slack or Discord webhook when they reach a checkpoint.
- **Manual Intervention**: Set `"human_approval": true` in `team.json` to pause the mission for manual feedback or correction via the terminal.

## 📦 Updated Dependencies
To support advanced document parsing and notifications, ensure your `requirements.txt` includes:
```text
crewai[docling]   # For .md, .docx, .pptx, .html
pandas            # For tabular data (.csv, .xlsx)
requests          # For Slack/Discord webhooks
pyyaml            # For .yaml configurations
```

## 👥 Expanded Agent Roster (`agents/`)

You can now orchestrate a full software development lifecycle team:
- **Librarian**: The data gatekeeper. Refreshes the ChromaDB index before missions start.
- **Solution Architect**: Designs modular patterns and system logic.
- **QA Engineer**: Writes and executes `pytest` suites using the Safe Terminal.
- **Technical Writer**: Generates professional documentation and README updates.
- **Project Manager**: Coordinates handoffs and ensures mission goals are met.

## 🛠️ Developing New Agents

> "Everything that has a beginning, has an end, Neo."

Adding a new agent to the Smith Stack is straightforward. Each agent must reside in the `agents/` folder and follow a standard functional signature to remain compatible with the dynamic loader.

### 1. Create the Agent File
Create a new file in `agent-app/agents/`, for example: `security_expert.py`.

### 2. Implement the `get_agent` Function
Every agent file **must** include a `get_agent(tools=None)` function. This allows `main.py` to inject dynamically loaded tools from the `tools/` folder based on your `team.json`.

```python
from crewai import Agent
import os

def get_agent(tools=None):
    """
    Standard signature for Smith Stack agents.
    :param tools: A list of tool objects passed by the dynamic loader.
    """
    return Agent(
        role="Security Expert",
        goal="Ensure all systems follow zero-trust protocols.",
        backstory="A veteran white-hat hacker specializing in local networks.",
        # Inherits the local model from your .env
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        # Assigns the tools provided by team.json
        tools=tools or [],
        # Recommended: Enable memory for long-term task consistency
        memory=True,
        verbose=True
    )
```

### 3. Register in `team.json`
Once the file is created, you do not need to restart the entire stack. Simply add the agent to your mission configuration:

```json
{
  "name": "security_expert",
  "tools": ["search_duckduckgo", "notifier"],
  "task_description": "Audit the current mission plan for potential data leaks.",
  "expected_output": "A security clearance report."
}
```

### Key Rules for Agent Parity:
- **`allow_knowledge_retrieval=True`**: Include this if the agent needs to access the RAG database (ChromaDB) via the Librarian's indexed files.
- **Sequential Context**: Because the stack uses a sequential process, your new agent will automatically have access to the "thoughts" and outputs of any agents listed before it in the `team.json`.


## 🛡️ License

>  "The future is our world, Morpheus. The future is our time"

This project is licensed under the **Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. 
