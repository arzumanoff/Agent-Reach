# -*- coding: utf-8 -*-
"""Agent Reach MCP server exposing read-only health/status."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from typing import Any

from agent_reach.config import Config
from agent_reach.core import AgentReach
from agent_reach.utils.text import scrub_url_credentials

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequestParams,
        CallToolResult,
        ListToolsResult,
        TextContent,
        Tool,
    )

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


_doctor_lock = threading.Lock()


def _doctor_report(eyes: AgentReach) -> str:
    """Serialize doctor runs because channel registry objects are shared."""
    with _doctor_lock:
        return eyes.doctor_report()


def create_server():
    if not HAS_MCP:
        print(
            "MCP not installed. Install: python -m pip install "
            "'agent-reach[mcp] @ "
            "https://github.com/Panniantong/agent-reach/archive/main.zip'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    config = Config(read_only=True)
    eyes = AgentReach(config)

    async def list_tools(_ctx: Any, _params: Any) -> ListToolsResult:
        return ListToolsResult(
            tools=[
                Tool(
                    name="get_status",
                    description=(
                        "Get Agent Reach status: which channels are installed "
                        "and active."
                    ),
                    input_schema={"type": "object", "properties": {}},
                )
            ]
        )

    async def call_tool(_ctx: Any, params: CallToolRequestParams) -> CallToolResult:
        try:
            if params.name == "get_status":
                result = await asyncio.to_thread(_doctor_report, eyes)
            else:
                result = f"Unknown tool: {params.name}"

            rendered = (
                json.dumps(result, ensure_ascii=False, indent=2)
                if isinstance(result, (dict, list))
                else str(result)
            )
            return CallToolResult(content=[TextContent(type="text", text=rendered)])
        except Exception as exc:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {scrub_url_credentials(exc)}",
                    )
                ],
                is_error=True,
            )

    return Server(
        "agent-reach",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def main():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
