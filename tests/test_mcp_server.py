"""Security boundaries for the optional Agent Reach MCP server."""

import asyncio
from types import SimpleNamespace

import agent_reach.integrations.mcp_server as mcp_server


class _FakeServer:
    def __init__(self, name, **handlers):
        self.name = name
        self.list_tools_handler = handlers.get("on_list_tools")
        self.call_tool_handler = handlers.get("on_call_tool")

    def create_initialization_options(self):
        return object()


def _install_fake_mcp(monkeypatch):
    monkeypatch.setattr(mcp_server, "HAS_MCP", True)
    monkeypatch.setattr(mcp_server, "Server", _FakeServer, raising=False)
    monkeypatch.setattr(
        mcp_server,
        "Tool",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )
    monkeypatch.setattr(
        mcp_server,
        "TextContent",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )
    monkeypatch.setattr(
        mcp_server,
        "ListToolsResult",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )
    monkeypatch.setattr(
        mcp_server,
        "CallToolResult",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )


def _params(name="get_status", arguments=None):
    return SimpleNamespace(name=name, arguments=arguments or {})


def test_mcp_status_uses_read_only_config(monkeypatch):
    _install_fake_mcp(monkeypatch)
    created_configs = []

    class _RecordingConfig:
        def __init__(self, *, read_only=False):
            self.read_only = read_only
            created_configs.append(self)

    class _AgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            return "ok"

    monkeypatch.setattr(mcp_server, "Config", _RecordingConfig)
    monkeypatch.setattr(mcp_server, "AgentReach", _AgentReach)

    server = mcp_server.create_server()
    result = asyncio.run(server.call_tool_handler(None, _params()))

    assert len(created_configs) == 1
    assert created_configs[0].read_only is True
    assert result.content[0].text == "ok"


def test_mcp_status_exception_credentials_are_scrubbed(monkeypatch):
    _install_fake_mcp(monkeypatch)

    class _Config:
        def __init__(self, *, read_only=False):
            self.read_only = read_only

    class _ExplodingAgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            raise RuntimeError(
                "request https://alice:password@example.test/data"
                "?token=top-secret failed"
            )

    monkeypatch.setattr(mcp_server, "Config", _Config)
    monkeypatch.setattr(mcp_server, "AgentReach", _ExplodingAgentReach)

    server = mcp_server.create_server()
    result = asyncio.run(server.call_tool_handler(None, _params()))
    text = result.content[0].text

    assert result.is_error is True
    assert "alice" not in text
    assert "password" not in text
    assert "top-secret" not in text
    assert "https://***@example.test/data?token=***" in text


def test_mcp_tool_schema_uses_modern_field_name(monkeypatch):
    _install_fake_mcp(monkeypatch)
    monkeypatch.setattr(mcp_server, "Config", lambda **kwargs: object())
    monkeypatch.setattr(
        mcp_server,
        "AgentReach",
        lambda config: SimpleNamespace(doctor_report=lambda: "ok"),
    )
    server = mcp_server.create_server()
    result = asyncio.run(server.list_tools_handler(None, None))
    assert result.tools[0].input_schema == {
        "type": "object",
        "properties": {},
    }
