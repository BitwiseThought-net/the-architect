# Progress log

## Session 1 - GitHub access for Open WebUI / LLM

Goal: automatically provide GitHub tooling (read repos by URL, issues, PRs) using
GitHub's official MCP server instead of the hand-written REST script.

### Done
- `Dockerfile.github-mcp`: copies `/server/github-mcp-server` from the official
  image into `ghcr.io/open-webui/mcpo`; versions are build args.
- `docker-compose.yml`: new `github-mcp` service (container `ai-github-mcp`),
  no published ports, `--strict-auth`, read-only by default, TCP healthcheck,
  autoheal label. `open-webui` gets a `TOOL_SERVER_CONNECTIONS` env entry that
  registers it as an OpenAPI tool server (bearer = MCPO_API_KEY).
- `.env.example`: GITHUB_PERSONAL_ACCESS_TOKEN, MCPO_API_KEY, GITHUB_TOOLSETS,
  GITHUB_READ_ONLY, optional version pins.
- Docs: new `docs/tools/github-mcp.md`; rows added to `docs/configuration/env-file.md`;
  index entry in `docs/README.md`; README setup step mentions the new required keys.
- `tests/test_compose_github_mcp.py`: static checks. New tests plus
  the rest of the suite pass (200 tests after retiring the old tool in session 2).
- Verified from mcpo 0.0.21 source: CLI stdio mode copies `os.environ` into the
  child (so the PAT reaches github-mcp-server); bearer auth; `--strict-auth` exists.

### Verified working (user confirmed)
- The mcpo + stdio design works end to end. With the external tool server added,
  attached to the model (Admin > Models) and enabled in a chat, Open WebUI's
  qwen3.8:latest called tools such as get_file_contents, list_commits,
  list_issues, list_releases and search_repositories on a GitHub repo URL.

### Vital setup steps (my instructions originally omitted #2)
1. Add the connection under Admin > Integrations > External Tool Servers
   (type OpenAPI, http://github-mcp:8000, Bearer = MCPO_API_KEY). Auto-registration
   via TOOL_SERVER_CONNECTIONS only applies to a fresh volume; do not rely on it.
2. Attach the tool to the model: Admin > Models > (defaults or specific model).
3. Enable it per chat from the + menu.
Integrations > External Tool Servers are NOT the Workspace Tools list.

### Corrections to earlier notes
- I once switched the repo to official-image `http` mode + native MCP, blaming
  an open-webui bug (#21805). That was premature and unproven: the real gap was
  step 2 above. That change was discarded; do NOT re-propose it unless the user
  asks. The OpenAPI/mcpo setup stays.
- Early 403s on /openapi.json meant the stored connection auth was not Bearer
  with the exact key; the proxy itself was fine.

### Known gotchas
- `TOOL_SERVER_CONNECTIONS` is a PersistentConfig (first boot only).
- Compose refuses to start unless PAT and MCPO_API_KEY are set. Consider a
  compose profile if GitHub should be optional.
- mcpo has no env var for its API key; it sits in the container command line.
- The user's first token had very broad classic scopes (admin:org, delete_repo...).
  Recommend a fine-grained read-only token.

### Working style notes
- Do not ask the user to re-run debug commands or repeat information; do not
  guess Open WebUI internals; do not make repo changes the user did not ask for.

### Session 3 - automatic provisioning (built, UNTESTED against a live instance)
- `scripts/install_tools.py` now also calls Open WebUI's API after installing
  tools: GET/POST `/api/v1/configs/tool_servers` (upsert the connection with
  info.id "github"), then GET `/api/v1/models/model?id=` and POST
  `/api/v1/models/model/update` or `/api/v1/models/create` to add `server:github`
  to `meta.toolIds` of each model in GITHUB_TOOL_MODELS (default MODEL_NAME).
  Endpoints and payload shapes were checked against Open WebUI `main` source, which
  may be newer than the user's image; failures only warn (see `docker compose logs
  tool-installer`).
- compose: tool-installer depends on github-mcp (healthy) and gets GITHUB_MCP_URL
  and GITHUB_TOOL_MODELS; MCPO_API_KEY/MODEL_NAME come from .env via env_file.
- tests/test_install_tools_github.py (fake Open WebUI) added; full suite 207 passed.
- Remaining manual step: enable the tool per chat from the + menu.
- Backup/migration advice given: copy webui.db (or the ai_open_webui_data volume);
  keep WEBUI_SECRET_KEY and MCPO_API_KEY identical; set a real WEBUI_SECRET_KEY
  (compose falls back to the literal "change-this-secret").

### Next steps
0. User to run `docker compose up` (or `docker compose run --rm tool-installer`),
   read `docker compose logs tool-installer`, and report whether registration and
   attachment worked; fix payload mismatches if warnings appear.
1. Pin GITHUB_MCP_VERSION and MCPO_VERSION now that a working pair exists.
2. DONE (session 2): retired tools/github_repo_tool.py, tests/test_github_repo_tool.py
   and doc references. tools/ now holds the agent tools plus web_scraper_tool.py.
   The installer never deletes tools, so the user must delete the old
   "GitHub Repository Reader" tool in Open WebUI (Workspace > Tools) by hand.
3. Optional: let the-architect agents use the MCP server (not wired today).
4. Docs stubs elsewhere still have TODOs; add github-mcp to
   docs/operations/docker-compose-services.md when completing it.
