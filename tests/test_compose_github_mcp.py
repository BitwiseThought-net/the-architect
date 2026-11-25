"""Static checks on the github-mcp service wiring in docker-compose.yml."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_github_mcp_not_published_to_host():
    assert "ports" not in COMPOSE["services"]["github-mcp"]


def test_github_mcp_requires_secrets_and_defaults_read_only():
    env = "\n".join(COMPOSE["services"]["github-mcp"]["environment"])
    assert "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN:?" in env
    assert "GITHUB_READ_ONLY=${GITHUB_READ_ONLY:-1}" in env
    cmd = COMPOSE["services"]["github-mcp"]["command"]
    assert any("MCPO_API_KEY:?" in str(c) for c in cmd)
    assert "--strict-auth" in cmd


def test_dockerfile_copies_upstream_binary():
    text = (ROOT / "Dockerfile.github-mcp").read_text()
    assert "/server/github-mcp-server" in text
    assert "ghcr.io/open-webui/mcpo" in text


def test_open_webui_registers_tool_server():
    entries = [e for e in COMPOSE["services"]["open-webui"]["environment"]
               if e.startswith("TOOL_SERVER_CONNECTIONS=")]
    assert len(entries) == 1
    raw = entries[0].split("=", 1)[1].replace("${MCPO_API_KEY:?set MCPO_API_KEY in .env}", "k")
    conn = json.loads(raw)[0]
    assert conn["url"] == "http://github-mcp:8000"
    assert conn["auth_type"] == "bearer"
