# The Architect

"Your life is the sum of a remainder of an unbalanced equation inherent to the programming of the matrix."

**The Architect** is a hardened, production-ready autonomous agent orchestration framework built on **CrewAI**. It is designed to manage complex multi-agent workflows with local LLM integration, dynamic "on-the-fly" configuration, and a modular plugin system for interactive communication via Discord.

## 🚀 Key Features

- **Local-First LLM Architecture**: Seamless integration with **Ollama** and **LiteLLM** for full data privacy and no API costs.
- **Dynamic Configuration**: Modify system settings (`config.json`) and agent team definitions (`team.json`) in real-time without restarting containers.
- **Modular Plugin System**: Self-contained Python plugins (e.g., Discord Bots, Notifications) that register tools and identity rules automatically.
- **System Librarian**: Automated RAG (Retrieval-Augmented Generation) indexing that synchronizes local documentation from the `/knowledge` folder into ChromaDB.
- **Hardened Execution**: Built-in retry logic, mission-level timeouts, and heartbeat monitoring for Docker auto-healing.
- **Sandboxed Execution**: Specialized tools for safe Python and Pytest execution within restricted directories.

---

## 🔄 Execution Lifecycle
1. **Infrastructure Check**: The system verifies that LiteLLM is ready and models are pulled.
2. **Knowledge Sync**: The **Librarian** scans `/knowledge` and updates the vector database.
3. **Team Assembly**: `team.json` is parsed, and agents are initialized with their tools and plugins.
4. **Mission Kickoff**: The crew executes tasks sequentially.
5. **Recovery/Idle**: If a task fails, the system retries based on `MAX_RETRIES` before entering a debug-friendly idle state.

---

## 🔒 The Sandbox Environment
To ensure system integrity, **The Architect** employs a "Safe-by-Design" approach for technical tasks:
- **Restricted Writes**: The `file_write_safe` tool strictly enforces that files are only written to the `/app/output` directory.
- **Command Whitelisting**: `terminal_safe` only permits `python` and `pytest` commands to prevent arbitrary shell execution.
- **Path Protection**: Any attempt at path traversal (`../`) is intercepted and blocked by the security auditors.

---

## 🛠 Debugging & Interaction
- **Live Logs**: View agent thoughts in real-time: `docker logs -f the-architect`.
- **Shell Access**: To inspect the container environment: `docker exec -it the-architect /bin/bash`.
- **Web UI**: Access the Open WebUI at `http://localhost:3011` to chat with your models directly outside of the agent workflow.

---

## 📂 Project Structure
- `agents/`: Python files defining agent roles (e.g., `coder.py`, `researcher.py`).
- `tools/`: Custom Python tools available to agents (e.g., `terminal_safe.py`).
- `loaders/`: File processors for the System Librarian (e.g., `pdf.py`, `csv.py`).
- `plugins/`: Self-contained feature modules (e.g., Discord integration).
- `knowledge/`: Raw data files (PDFs, TXT) for RAG indexing.
- `output/`: The designated sandbox where agents save mission results.

---

## 🛠 Installation

### Prerequisites
- **Docker & Docker Compose**
- **NVIDIA Container Toolkit** (for GPU acceleration)
- **Jenkins** (optional, for CI/CD deployment)

### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd the-architect
   ```

2. **Initialize Configuration:**
   Copy the example files to create your active configuration:
   ```bash
   cp config.json.example config.json
   cp team.json.example team.json
   cp plugins/discord_bot.py.example plugins/discord_bot.py
   cp plugins/discord_notifications.py.example plugins/discord_notifications.py
   ```

3. **Launch the System:**
   ```bash
   docker compose up -d --build
   ```

---

## ⚙️ Configuration

### 1. `config.json` (System Settings)
Controls the global behavior of the machine. Changes are applied on the next agent action.


| Key | Description | Default |
| :--- | :--- | :--- |
| `MODEL_NAME` | The primary LLM model used by agents. | `qwen3.6:latest` |
| `EMBEDDING_MODEL` | The model used for RAG/Knowledge indexing. | `nomic-embed-text` |
| `TEMPERATURE` | Controls LLM creativity (0.0 = deterministic). | `0.3` |
| `MAX_TOKENS` | Maximum response length per agent call. | `4096` |
| `MAX_RETRIES` | Number of times to retry a failed mission. | `3` |
| `MISSION_TIMEOUT_SECONDS`| Hard cutoff for total mission duration. | `1800` |
| `VERBOSE` | Toggles detailed agent "thought" logs. | `true` |

### 2. `team.json` (Agent Definitions)
Defines the "Who" and "What" of your current mission.
- **active_agents**: A list of agent objects including their `name`, `task_description`, and assigned `tools`.

### 3. `.env` (Infrastructure)
Used for fixed networking and boot-level security.
- `LITELLM_PORT`: Port for the LiteLLM proxy (default `4000`).
- `UI_PORT`: Port for the Open WebUI (default `3011`).
- `WEBUI_SECRET_KEY`: Security key for the WebUI session.

---

## 🔌 Plugins

The Architect supports "Hot-Swappable" Python plugins. Drop a `.py` file into the `/plugins` directory to enable new capabilities.

### Discord Bot (`plugins/discord_bot.py`)
Allows you to interact with agents via Slash Commands.
- **Identity Enforcement**: Automatically prepends `agent_name: ` to responses.
- **Interactive**: Supports real-time status updates from the crew.

### Discord Notifications (`plugins/discord_notifications.py`)
Provides a `send_notification` tool for outbound system alerts via Webhooks.

---

## 📚 Knowledge Management

Place any technical documentation (`.txt`, `.pdf`, `.csv`, etc.) into the `/knowledge` directory.
- The **System Librarian** will automatically detect these files.
- It uses the corresponding loader in `/loaders` to index the content.
- Agents with `allow_knowledge_retrieval=True` can then query this data during missions.

---

## 🛡️ Resilience & Health

- **Heartbeat**: The system writes to `/tmp/heartbeat` every loop.
- **Autoheal**: Docker monitors the heartbeat; if the process stalls for more than 5 minutes, the container is automatically restarted.
- **Idle State**: If a mission reaches `MAX_RETRIES`, the container stays alive in an "Idle" state to allow log inspection and debugging.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code standards and plugin development.

---

## 🛡️ License

This project is [licensed](LICENSE.md) under the **Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. 


*"Ergo, the concordance of thought is established."*
