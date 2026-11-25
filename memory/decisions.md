# Design decisions

- **mcpo + stdio binary, not HTTP mode.** Keeps the GitHub PAT inside one
  container; Open WebUI only holds the mcpo key. Cost: extra proxy layer, a
  custom Dockerfile, and OpenAPI (no Open WebUI tool events).
- **Read-only by default** (`GITHUB_READ_ONLY=1`); writes are an explicit opt-in.
- **Narrow toolsets** (repos, issues, pull_requests) to save model context.
- **No host port** for github-mcp; internal network only.
- **Secrets only in .env** (git-ignored), required via Compose `:?`; the
  user's draft hardcoded the mcpo key in compose, which was replaced.
- **Floating image tags by default, pinnable via .env** so the first build works.

- **Stay on mcpo/OpenAPI (confirmed working).** The native-MCP/`http` alternative
  was explored and discarded; it is only worth revisiting if mcpo causes trouble.
- **Registration is a documented manual three-step** (connection, attach to model,
  enable in chat); first-boot env registration is a bonus, not a guarantee.
- **Old `tools/github_repo_tool.py` retired** (user decision); GitHub access is the
  github-mcp service only.
