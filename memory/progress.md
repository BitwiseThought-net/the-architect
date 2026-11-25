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
  tests/test_github_repo_tool.py pass (21). Full suite was not run.
- Verified from mcpo 0.0.21 source: CLI stdio mode copies `os.environ` into the
  child (so the PAT reaches github-mcp-server); bearer auth; `--strict-auth` exists.

### NOT verified (no Docker daemon or ghcr.io access in the authoring sandbox)
- Image build, container startup, and that `:main` mcpo supports `--strict-auth`.
- That `TOOL_SERVER_CONNECTIONS` with `"type":"openapi"` matches the current Open
  WebUI schema. Fallback is adding the connection in Admin > Integrations.
- Real tool calls against GitHub.

### Known gotchas
- `TOOL_SERVER_CONNECTIONS` is a PersistentConfig: only read on first boot of a
  fresh `ai_open_webui_data` volume. Rotating MCPO_API_KEY later needs a UI edit.
- Compose now refuses to start unless PAT and MCPO_API_KEY are set (same pattern
  as ADMIN_PASSWORD). Consider a compose profile if GitHub should be optional.
- mcpo has no env var for its API key; it sits in the container command line.

### Next steps
1. Run `docker compose up -d --build github-mcp`, check logs, run the curl/python
   check in docs/tools/github-mcp.md, then test a chat ("summarize github.com/o/r").
2. Pin GITHUB_MCP_VERSION and MCPO_VERSION once a working pair is confirmed.
3. Decide whether to retire `tools/github_repo_tool.py` (and its tests/docs).
4. Optional: let the-architect agents use the same server (they cannot today;
   the MCP service is only wired to Open WebUI).
5. Alternative worth evaluating: official image in `http` mode with Open WebUI's
   native MCP (Streamable HTTP), removing mcpo and the custom Dockerfile, at the
   cost of storing the PAT in Open WebUI. Confirm the `http` subcommand exists in
   a pinned release first.
6. Docs stubs elsewhere (docker-compose-services.md, open-webui-tools.md) still
   have TODOs; add github-mcp to docker-compose-services.md when completing it.
