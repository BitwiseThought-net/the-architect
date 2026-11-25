# Open WebUI Tools

> Status: stub. See `docs/LLM_DOCS.prompt.md` for how to complete this page.

## TODO

- Explain this is the second of the two distinct "tool" systems in the repo
  (see the project-wide note in `docs/LLM_DOCS.prompt.md`): these are Open WebUI
  plugin-style Python modules (a `Tools` class with a nested `Valves`
  pydantic model, and a docstring frontmatter with `title`/`author`/
  `description`/`version`), installed directly into the Open WebUI chat
  interface - not wired into `team.json` agents. Contrast briefly with
  `docs/tools/agent-tools.md` and link to it.
- Note that GitHub access is no longer a custom Open WebUI Tool: the old
  `github_repo_tool.py` was retired in favor of the `github-mcp` service. Link to
  [GitHub MCP Tools](github-mcp.md).
- Document `tools/web_scraper_tool.py` fully:
  - What it does: fetches a URL and returns cleaned plain-text content
    (script/style/markup stripped via BeautifulSoup).
  - Its `Valves`: `MAX_CHARS` (default `8000`), `TIMEOUT` (default `15`
    seconds, request timeout). Read the full file to confirm exact
    truncation/error-handling behavior before writing this section.
  - Its public method `scrape_web_page(url)`, required `http(s)://` prefix
    validation, and error return format.
- Document the installation mechanism end-to-end:
  `scripts/install_tools.py`, run by the `tool-installer` Compose service
  (`docker-compose.yml`), which: waits for Open WebUI's `/health` endpoint,
  signs up (or signs in as a fallback) an admin account from
  `ADMIN_EMAIL`/`ADMIN_PASSWORD`/`ADMIN_NAME`, then POSTs every `.py` file
  in `/tools` (mounted read-only from the repo's `tools/` dir) to Open
  WebUI's Tools API - deriving each tool's id from its filename and its
  display name/description from the docstring frontmatter. Document that it
  is idempotent/non-destructive: it **skips** (never overwrites) a tool id
  that already exists in Open WebUI, and the documented way to push a source
  change is to delete the tool in Open WebUI first (or give it a new id)
  and re-run. Also document its own env vars: `OPEN_WEBUI_URL`,
  `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`, `TOOLS_DIR` (default
  `/tools`).
