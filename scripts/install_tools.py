"""
Installs (or updates) the web scraper Tool (and any other .py file in /tools) into Open
WebUI over its REST API, so no manual copy/paste into the UI is needed.

Reads every .py file in /tools, pulls a title/description out of its leading
docstring frontmatter, and POSTs it to Open WebUI's tools API. If a tool with
that id already exists, it is left alone and skipped, this script never
overwrites an existing tool. To push a source change to a tool that's
already installed, delete it in Open WebUI first (or give it a new id),
then re-run.

Configured entirely through environment variables (see docker-compose.yml):
  OPEN_WEBUI_URL   base URL of Open WebUI, e.g. http://open-webui:8080
  ADMIN_EMAIL      email for the account that will own these tools
  ADMIN_PASSWORD   password for that account
  ADMIN_NAME       display name, only used if the account doesn't exist yet
  TOOLS_DIR        directory containing the .py tool files (default /tools)

GitHub (optional, runs after the tools are installed; failures only warn):
  MCPO_API_KEY       bearer key of the github-mcp (mcpo) service. If unset, the
                     GitHub steps are skipped.
  GITHUB_MCP_URL     base URL of that service (default http://github-mcp:8000)
  GITHUB_TOOL_MODELS comma-separated Open WebUI model ids that should get the
                     GitHub tool attached (default: MODEL_NAME)

It registers (or updates) one External Tool Server connection with id "github"
and attaches it to those models (meta.toolIds = "server:github"), the same
two things you would otherwise do by hand in Admin Settings > Integrations and
Admin Settings > Models. Other connections and tool ids are left untouched.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OPEN_WEBUI_URL = os.environ.get("OPEN_WEBUI_URL", "http://open-webui:8080").rstrip("/")
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Admin")
TOOLS_DIR = os.environ.get("TOOLS_DIR", "/tools")

GITHUB_SERVER_ID = "github"
GITHUB_TOOL_ID = f"server:{GITHUB_SERVER_ID}"

MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 3


def request(method, path, token=None, payload=None):
    url = f"{OPEN_WEBUI_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body}


def wait_for_server():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            status, _ = request("GET", "/health")
            if status == 200:
                return
        except Exception:
            pass
        print(f"Waiting for Open WebUI to be reachable... ({attempt}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY_SECONDS)
    print("Open WebUI never became reachable, giving up.")
    sys.exit(1)


def get_admin_token():
    # First run: this creates the account (and it becomes admin, since it's
    # the first user). Later runs: signup fails because the account already
    # exists, so fall back to signing in with the same credentials.
    status, body = request(
        "POST", "/api/v1/auths/signup",
        payload={"name": ADMIN_NAME, "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if status == 200 and "token" in body:
        print(f"Created admin account {ADMIN_EMAIL}.")
        return body["token"]

    status, body = request(
        "POST", "/api/v1/auths/signin",
        payload={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if status == 200 and "token" in body:
        print(f"Signed in as {ADMIN_EMAIL}.")
        return body["token"]

    print(f"Could not authenticate as {ADMIN_EMAIL}: {body}")
    sys.exit(1)


def parse_frontmatter(content):
    """Pull title/description out of the module's leading docstring, if present."""
    match = re.match(r'\s*"""(.*?)"""', content, re.DOTALL)
    title, description = None, None
    if match:
        block = match.group(1)
        t = re.search(r"^title:\s*(.+)$", block, re.MULTILINE)
        d = re.search(r"^description:\s*(.+)$", block, re.MULTILINE)
        if t:
            title = t.group(1).strip()
        if d:
            description = d.group(1).strip()
    return title, description


def tool_exists(token, tool_id):
    status, _ = request("GET", f"/api/v1/tools/id/{tool_id}", token=token)
    return status == 200


def install_tool(token, filepath):
    filename = os.path.basename(filepath)
    tool_id = re.sub(r"[^a-z0-9_]", "_", filename[:-3].lower())

    if tool_exists(token, tool_id):
        print(f"Tool '{tool_id}' already exists, skipping (not overwriting).")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    title, description = parse_frontmatter(content)
    name = title or tool_id
    payload = {
        "id": tool_id,
        "name": name,
        "content": content,
        "meta": {"description": description or ""},
    }

    status, body = request("POST", "/api/v1/tools/create", token=token, payload=payload)
    if status == 200:
        print(f"Installed tool '{name}' (id={tool_id}).")
        return

    if status == 400 and "taken" in json.dumps(body).lower():
        # Lost a race with something else that created it between our check
        # and this request. Treat it the same as "already exists": skip.
        print(f"Tool '{tool_id}' already exists (created concurrently), skipping.")
        return

    print(f"Failed to install tool '{name}' (id={tool_id}): status={status} body={body}")
    sys.exit(1)


def register_github_tool_server(token):
    """Create or update the External Tool Server connection for github-mcp.

    Returns True if the connection is in place afterwards. Only the entry whose
    info.id is "github" is managed; every other connection is preserved.
    """
    key = os.environ.get("MCPO_API_KEY", "").strip()
    if not key:
        print("MCPO_API_KEY is not set, skipping GitHub tool server registration.")
        return False
    url = os.environ.get("GITHUB_MCP_URL", "http://github-mcp:8000").rstrip("/")

    status, body = request("GET", "/api/v1/configs/tool_servers", token=token)
    if status != 200:
        print(f"WARNING: could not read tool server config: status={status} body={body}")
        return False
    connections = list(body.get("TOOL_SERVER_CONNECTIONS") or [])

    index = next(
        (i for i, c in enumerate(connections)
         if (c.get("info") or {}).get("id") == GITHUB_SERVER_ID),
        None,
    )
    existing = connections[index] if index is not None else {}
    desired = {
        **existing,
        "type": "openapi",
        "url": url,
        "path": "openapi.json",
        "auth_type": "bearer",
        "key": key,
        "config": {**(existing.get("config") or {}), "enable": True},
        "info": {
            **(existing.get("info") or {}),
            "id": GITHUB_SERVER_ID,
            "name": "GitHub",
            "description": "Official GitHub MCP server: read repos, issues, pull requests",
        },
    }
    if existing == desired:
        print("GitHub tool server connection already up to date.")
        return True

    if index is None:
        connections.append(desired)
    else:
        connections[index] = desired

    status, body = request(
        "POST", "/api/v1/configs/tool_servers", token=token,
        payload={"TOOL_SERVER_CONNECTIONS": connections},
    )
    if status != 200:
        print(f"WARNING: could not save tool server config: status={status} body={body}")
        return False
    print(f"Registered GitHub tool server connection ({url}).")
    return True


def attach_tool_to_model(token, model_id, tool_id=GITHUB_TOOL_ID):
    """Add tool_id to the model's meta.toolIds, creating the model entry if needed."""
    path = "/api/v1/models/model?id=" + urllib.parse.quote(model_id, safe="")
    status, existing = request("GET", path, token=token)

    if status == 200 and existing:
        meta = dict(existing.get("meta") or {})
        tool_ids = list(meta.get("toolIds") or [])
        if tool_id in tool_ids:
            print(f"Model '{model_id}' already has {tool_id}, skipping.")
            return True
        meta["toolIds"] = tool_ids + [tool_id]
        form = {
            "id": existing.get("id", model_id),
            "base_model_id": existing.get("base_model_id"),
            "name": existing.get("name") or model_id,
            "meta": meta,
            "params": existing.get("params") or {},
            "is_active": existing.get("is_active", True),
        }
        status, body = request("POST", "/api/v1/models/model/update", token=token, payload=form)
    elif status in (401, 404):
        # No workspace entry for this model yet. Create one that only adds the
        # tool, and keep it readable by everyone: a base model without an
        # entry is visible to all users, so the new entry must not hide it.
        form = {
            "id": model_id,
            "base_model_id": None,
            "name": model_id,
            "meta": {"toolIds": [tool_id]},
            "params": {},
            "is_active": True,
            "access_grants": [
                {"principal_type": "user", "principal_id": "*", "permission": "read"}
            ],
        }
        status, body = request("POST", "/api/v1/models/create", token=token, payload=form)
    else:
        print(f"WARNING: could not look up model '{model_id}': status={status} body={existing}")
        return False

    if status != 200:
        print(f"WARNING: could not attach {tool_id} to model '{model_id}': status={status} body={body}")
        return False
    print(f"Attached {tool_id} to model '{model_id}'.")
    return True


def setup_github_tool(token):
    """Register the GitHub tool server and attach it to the configured models.

    Never raises: the GitHub steps are best effort and must not stop the tool
    installation above from counting as done.
    """
    try:
        if not register_github_tool_server(token):
            return
        raw = os.environ.get("GITHUB_TOOL_MODELS") or os.environ.get("MODEL_NAME", "")
        models = [m.strip() for m in raw.split(",") if m.strip()]
        if not models:
            print("WARNING: no models to attach the GitHub tool to "
                  "(set GITHUB_TOOL_MODELS or MODEL_NAME). Attach it in Admin Settings > Models.")
            return
        for model_id in models:
            attach_tool_to_model(token, model_id)
    except Exception as e:  # noqa: BLE001 - best effort by design
        print(f"WARNING: GitHub tool setup failed: {e}")


def main():
    wait_for_server()
    token = get_admin_token()

    tool_files = sorted(
        os.path.join(TOOLS_DIR, f) for f in os.listdir(TOOLS_DIR) if f.endswith(".py")
    )
    if not tool_files:
        print(f"No .py tool files found in {TOOLS_DIR}.")
    for filepath in tool_files:
        install_tool(token, filepath)

    setup_github_tool(token)
    print("Done.")


if __name__ == "__main__":
    main()

