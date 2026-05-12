# Contributing to The Architect

Thank you for your interest in contributing to **The Architect** (`the-architect`). This document establishes the strict architectural constraints, code style standards, and framework abstraction protocols required to keep the system decoupled, hot-swappable, and secure.

---

## 🏛️ Abstraction Architecture Paradigm

The Architect utilizes a strict **Abstract Factory Pattern** nested within the `ai_layer/` package. The core engine (`main.py`) must *never* import third-party orchestration libraries (e.g., `crewai`, `autogen`, `langgraph`, `smolagents`) directly. Instead, all functionality is exposed through a unified interface.

### The Unified Interface Boundary
Every framework factory module dropped into `ai_layer/` MUST expose the following five core primitives with identical class signatures or functional wrappers:
1. `Agent`: Class initialization mapping role, goal, backstory, tools, and LLM configs.
2. `Task`: Class initialization wrapping description strings, expected output formats, and targeting.
3. `Crew`: Pipeline runtime loop wrapper executing the workflow sequentially via `.kickoff()`.
4. `LLM`: Centralized model wrapper mapping model names, temperatures, and custom proxy endpoints.
5. `tool`: A standard function decorator (`@tool`) to register execution logic.

---

## 🛠️ Step-by-Step Factory Integration Protocol

When contributing an adapter module for a new AI agent framework (e.g., adding `ai_layer/new_framework.py`), follow this exact protocol:

### Step 1: Create the Isolated Adapter Module
Create a single, self-contained Python file inside the `ai_layer/` directory named after the framework (e.g., `ai_layer/my_framework.py`). 
* No framework-specific imports are allowed outside of this file.
* Wrap native initialization properties within unified proxy class definitions.

### Step 2: Implement the Core Primitives
Ensure your factory connector translates standard properties natively. For example, if the framework handles tools via function definitions, use reflective parameters (`inspect.signature`) to build schemas dynamically:

```python
# Signature Guide for ai_layer/my_framework.py
class LLM:
    def __init__(self, model, base_url, api_key, temperature=0.3, max_tokens=4096, **kwargs):
        # Translate settings into native engine configurations here
        pass

class Agent:
    def __init__(self, role, goal, backstory, llm, tools=None, **kwargs):
        # Convert role, goal, and backstory into system prompts natively
        pass

class Task:
    def __init__(self, description, expected_output, agent, **kwargs):
        # Combine descriptions and output formats cleanly
        pass

class Crew:
    def __init__(self, agents, tasks, verbose=True, **kwargs):
        self.agents = agents
        self.tasks = tasks
        
    def kickoff(self) -> str:
        # Loop through tasks sequentially and return string outputs
        return "Workflow completed."

def tool(*args, **kwargs):
    def decorator(func):
        # Attach name and description metadata mirrors natively
        return func
    return decorator
```

### Step 3: Register Interface Stubs & Proxies
To prevent runtime import crashes across global workflows when your new framework is active, you must include proxy tokens for system-level tools and ingestion loaders:

```python
# Implement these empty or placeholder attributes inside your factory module
class Knowledge:
    CSV = object; Docling = object; JSON = object
    Excel = object; TextFile = object; XML = object

class DuckDuckGoSearchTool:
    def __init__(self, *args, **kwargs):
        self.name = "duckduckgo_search"
```

### Step 4: Whitelist the Factory Registry
Update the configuration validation array inside the central gateway wrapper (**`ai_layer/orchestrator.py`**) to accept your new identifier token:

```python
# Append your exact filename token to the available array matrix
available_frameworks = ["crewai", "autogen", "langgraph", "smolagents", "my_framework"]
```

---

## 🔒 Security & Sandbox Constraints

Custom tools and plugins must maintain absolute compliance with the zero-trust execution boundaries enforced across the system:

1. **Confinement Safety**: Tools manipulating data arrays must explicitly read from `get_config_value("SAFE_OUTPUT_DIR", "/app/output")` to ensure file writes are locked inside the container sandbox.
2. **Command Whitelisting**: Terminal tools must match commands against strict string-prefix verification lists (`python `, `pytest `, `python3 `) before using local subprocess layers.
3. **Hot-Swapping Compliance**: Plugins must reload on-demand using `importlib.reload(module)` loops inside `main.py`. Avoid caching state or configurations in memory.

---

## 📜 Code Style & Git Cleanliness

* **Dependency Tracking**: If your factory requires new packages, append them cleanly to `requirements.txt` with strict version freezes. Do not overwrite core library structures.
* **Metadata Uniformity**: All components must pass explicit parameter maps (`"source"`, `"type"`) inside their metadata payloads.
* **Credential Protection**: Never check in active tokens, secret environments, or functional `.py` files containing private credentials. Ensure your active scripts are matched against the local `.gitignore` specifications before executing a push command.

---

## 🚀 Pull Request Checklist

Before submitting a Pull Request to merge updates into the `main` branch, verify:
- [ ] Your code introduces zero direct `crewai`, `autogen`, or third-party agent engine strings outside its isolated factory file.
- [ ] The `grep -r "crewai" . | grep -v "ai_layer"` structural pass yields completely empty results.
- [ ] Your logic is fully compatible with targeted terminal overrides (`python main.py --agent <name> "command"`).
- [ ] Container tests compile safely with the updated string-block healthcheck syntax.
