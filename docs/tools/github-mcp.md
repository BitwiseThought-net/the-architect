# GitHub MCP Tools

This page covers the `github-mcp` Compose service, which gives Open WebUI (and
the model behind it) access to GitHub through GitHub's official MCP server. It
runs the official `github-mcp-server` binary in stdio mode behind `mcpo`, Open
WebUI's MCP-to-OpenAPI proxy, and is registered in Open WebUI automatically on
first boot. It supplements, and can eventually replace, the hand-written
`tools/github_repo_tool.py` described in [Open WebUI Tools](open-webui-tools.md).

## How it fits together

```text
Open WebUI --(OpenAPI + Bearer MCPO_API_KEY)--> github-mcp (mcpo) --stdio--> github-mcp-server --(PAT)--> api.github.com
```

- The GitHub token lives only in the `github-mcp` container. Open WebUI holds
  only the `MCPO_API_KEY`, which is useless outside the Compose network.
- The service publishes no host port. Only containers on the Compose network
  can reach `http://github-mcp:8000`.
- Referencing a repo by URL works because the model reads the owner and repo
  from the URL you paste and calls the server's tools (file contents, search,
  issues, pull requests) with them.

## Configuration

All keys go in `.env` (see [`.env` Reference](../configuration/env-file.md)).

| Key | Default | Purpose |
|---|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | required | Token used for every GitHub call. Prefer a fine-grained token scoped to specific repos. |
| `MCPO_API_KEY` | required | Bearer key Open WebUI must present to mcpo. |
| `GITHUB_TOOLSETS` | `repos,issues,pull_requests` | Which toolsets the server loads. Fewer toolsets means less context for the model. |
| `GITHUB_READ_ONLY` | `1` | `1` hides every write tool. Set `0` to allow creating issues and pull requests. |
| `GITHUB_MCP_VERSION` | `latest` | Tag of `ghcr.io/github/github-mcp-server` copied into the image. |
| `MCPO_VERSION` | `main` | Tag of `ghcr.io/open-webui/mcpo` used as the base image. |

## Open WebUI registration

The `open-webui` service receives a `TOOL_SERVER_CONNECTIONS` entry pointing at
`http://github-mcp:8000` with the `MCPO_API_KEY` as bearer key. Open WebUI treats
this as a persistent config value: it is read on the first boot of a fresh data
volume only. If Open WebUI already has data, or you rotate `MCPO_API_KEY`,
update the connection by hand under Settings > Admin > Integrations (type
OpenAPI, URL `http://github-mcp:8000`, auth Bearer). Then enable the GitHub tool
in a chat from the tools menu.

## Token and write-access guidance

1. Start read-only (the default) and a fine-grained token with Contents, Metadata
   and Pull requests read access.
2. To let the model open issues or pull requests, set `GITHUB_READ_ONLY=0` and
   grant that token Issues and Pull requests write access, then run
   `docker compose up -d --build github-mcp`.
3. The token is shared by every Open WebUI user. Do not enable signup for
   untrusted users while write access is on.

## Verifying

```bash
docker compose up -d --build github-mcp
docker compose logs github-mcp
docker compose exec open-webui python3 -c "import urllib.request,os; r=urllib.request.Request('http://github-mcp:8000/openapi.json', headers={'Authorization':'Bearer '+os.environ['MCPO_API_KEY']}); print(urllib.request.urlopen(r).status)"
```

A `200` means Open WebUI can reach the proxy with the key.
