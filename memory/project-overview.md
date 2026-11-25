# Project overview: The Architect

Local-first multi-agent framework. Python app (`main.py`, `ai_layer/`, `agents/`,
`tools/`, `ai_io/`, `loaders/`) runs CrewAI/smolagents (AutoGen/LangGraph are
`.py.example`) against Ollama via LiteLLM, with ChromaDB for RAG.

## Docker Compose services (docker-compose.yml)
autoheal, the-architect, tool-installer (one-shot, runs scripts/install_tools.py),
open-webui, litellm, searxng, chromadb, ollama, and (new) github-mcp.

## Two separate "tool" systems
- Agent tools: `tools/*.py` wired through `team.json` (see docs/tools/agent-tools.md).
- Open WebUI tools: `tools/github_repo_tool.py`, `tools/web_scraper_tool.py`
  (a `Tools` class with `Valves`), auto-installed by `scripts/install_tools.py`.
  The installer skips tools whose id already exists.

## Conventions
- Config priority: config.json, then .env, then defaults (lib/utils.py).
- Docs: `docs/LLM_DOCS.prompt.md` is the doc-writing instruction set. Stubs have
  a `## TODO`; finished pages open with a summary. Use hyphens, never em dashes.
- Tests: `pytest` (tests/), CI in .github/workflows/tests.yml.
- No `memory/` folder existed before this session; it was created here.
