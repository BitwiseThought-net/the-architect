"""Tests for the GitHub registration/attachment steps in scripts/install_tools.py,
using an in-memory fake of the Open WebUI endpoints involved."""
import importlib.util
import os
import urllib.parse
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def mod(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "a@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "pw")
    monkeypatch.setenv("MCPO_API_KEY", "secret-key")
    monkeypatch.setenv("MODEL_NAME", "qwen3.8:latest")
    monkeypatch.delenv("GITHUB_TOOL_MODELS", raising=False)
    spec = importlib.util.spec_from_file_location("install_tools", ROOT / "scripts" / "install_tools.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class FakeWebUI:
    def __init__(self, connections=None, models=None):
        self.connections = list(connections or [])
        self.models = dict(models or {})
        self.calls = []

    def __call__(self, method, path, token=None, payload=None):
        self.calls.append((method, path, payload))
        if (method, path) == ("GET", "/api/v1/configs/tool_servers"):
            return 200, {"TOOL_SERVER_CONNECTIONS": self.connections}
        if (method, path) == ("POST", "/api/v1/configs/tool_servers"):
            self.connections = payload["TOOL_SERVER_CONNECTIONS"]
            return 200, payload
        if method == "GET" and path.startswith("/api/v1/models/model?id="):
            mid = urllib.parse.unquote(path.split("=", 1)[1])
            return (200, self.models[mid]) if mid in self.models else (404, {"detail": "nf"})
        if (method, path) in (("POST", "/api/v1/models/create"), ("POST", "/api/v1/models/model/update")):
            self.models[payload["id"]] = payload
            return 200, payload
        return 500, {"detail": "unexpected " + path}


def test_registers_connection_and_is_idempotent(mod, monkeypatch):
    fake = FakeWebUI()
    monkeypatch.setattr(mod, "request", fake)
    assert mod.register_github_tool_server("t") is True
    conn = fake.connections[0]
    assert conn["url"] == "http://github-mcp:8000"
    assert conn["auth_type"] == "bearer" and conn["key"] == "secret-key"
    assert conn["info"]["id"] == "github" and conn["config"]["enable"] is True
    posts = [c for c in fake.calls if c[0] == "POST"]
    assert mod.register_github_tool_server("t") is True
    assert len(fake.connections) == 1
    assert [c for c in fake.calls if c[0] == "POST"] == posts  # no second write


def test_updates_own_entry_and_keeps_others(mod, monkeypatch):
    other = {"url": "http://other", "path": "openapi.json", "auth_type": "none", "key": "",
             "config": {"enable": True}, "info": {"id": "other"}}
    old = {"url": "http://old", "path": "x", "auth_type": "session", "key": "bad",
           "config": {"enable": False, "custom": 1}, "info": {"id": "github"}}
    fake = FakeWebUI(connections=[other, old])
    monkeypatch.setattr(mod, "request", fake)
    mod.register_github_tool_server("t")
    assert fake.connections[0] == other
    assert len(fake.connections) == 2
    updated = fake.connections[1]
    assert updated["key"] == "secret-key" and updated["auth_type"] == "bearer"
    assert updated["config"] == {"enable": True, "custom": 1}


def test_skips_without_api_key(mod, monkeypatch):
    monkeypatch.delenv("MCPO_API_KEY")
    fake = FakeWebUI()
    monkeypatch.setattr(mod, "request", fake)
    assert mod.register_github_tool_server("t") is False
    assert fake.calls == []


def test_attach_creates_missing_model_with_public_read(mod, monkeypatch):
    fake = FakeWebUI()
    monkeypatch.setattr(mod, "request", fake)
    assert mod.attach_tool_to_model("t", "qwen3.8:latest") is True
    m = fake.models["qwen3.8:latest"]
    assert m["meta"]["toolIds"] == ["server:github"]
    assert m["base_model_id"] is None
    assert m["access_grants"][0]["principal_id"] == "*"


def test_attach_merges_into_existing_model_once(mod, monkeypatch):
    existing = {"id": "m", "name": "My Model", "base_model_id": None, "is_active": True,
                "meta": {"toolIds": ["web_scraper_tool"], "description": "d"}, "params": {"x": 1}}
    fake = FakeWebUI(models={"m": existing})
    monkeypatch.setattr(mod, "request", fake)
    assert mod.attach_tool_to_model("t", "m") is True
    assert fake.models["m"]["meta"]["toolIds"] == ["web_scraper_tool", "server:github"]
    assert fake.models["m"]["meta"]["description"] == "d"
    assert fake.models["m"]["params"] == {"x": 1}
    n = len(fake.calls)
    assert mod.attach_tool_to_model("t", "m") is True
    assert all(c[0] == "GET" for c in fake.calls[n:])  # already attached: no write


def test_setup_attaches_to_all_listed_models_and_never_raises(mod, monkeypatch):
    monkeypatch.setenv("GITHUB_TOOL_MODELS", "a, b")
    fake = FakeWebUI()
    monkeypatch.setattr(mod, "request", fake)
    mod.setup_github_tool("t")
    assert set(fake.models) == {"a", "b"}

    def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(mod, "request", boom)
    mod.setup_github_tool("t")  # must not raise
