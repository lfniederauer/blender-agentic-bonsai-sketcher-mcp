# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Shared MCP client helpers for tests (stdio subprocess or streamable HTTP).
"""

__all__ = (
    "mcp_http_url",
    "running_in_docker_tests",
    "query_server",
    "call_server_tool",
)

import asyncio
import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MCP_DIR = os.path.join(_REPO_DIR, "mcp")


def mcp_http_url() -> str | None:
    """
    Return the HTTP MCP base URL when configured, else ``None``.
    """
    url = os.environ.get("BLENDER_MCP_HTTP_URL", "").strip()
    if not url:
        return None
    if not url.endswith("/"):
        url += "/"
    return url


def running_in_docker_tests() -> bool:
    """
    True when the test harness runs inside the Docker test image.
    """
    return os.environ.get("BLENDER_MCP_TEST_IN_DOCKER", "").lstrip("0") != ""


def _server_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = _MCP_DIR
    port = os.environ.get("BLENDER_MCP_PORT")
    if port:
        env["BLENDER_MCP_PORT"] = port
    host = os.environ.get("BLENDER_MCP_HOST")
    if host:
        env["BLENDER_MCP_HOST"] = host
    blender_path = os.environ.get("BLENDER_PATH")
    if blender_path:
        env["BLENDER_PATH"] = blender_path
    return env


@asynccontextmanager
async def _mcp_session() -> AsyncIterator[ClientSession]:
    url = mcp_http_url()
    if url is not None:
        try:
            from mcp.client.streamable_http import streamable_http_client
        except ImportError:  # pragma: no cover - older MCP SDK
            from mcp.client.streamable_http import streamablehttp_client as streamable_http_client  # type: ignore

        async with streamable_http_client(url) as streams:
            read, write = streams[0], streams[1]
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "blmcp"],
            env=_server_env(),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def _query_server_async() -> dict[str, Any]:
    url = mcp_http_url()
    if url is not None:
        try:
            from mcp.client.streamable_http import streamable_http_client
        except ImportError:  # pragma: no cover
            from mcp.client.streamable_http import streamablehttp_client as streamable_http_client  # type: ignore

        async with streamable_http_client(url) as streams:
            read, write = streams[0], streams[1]
            async with ClientSession(read, write) as session:
                init_result = await session.initialize()
                tools_result = await session.list_tools()
                return _format_server_query(init_result, tools_result)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "blmcp"],
        env=_server_env(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            tools_result = await session.list_tools()
            return _format_server_query(init_result, tools_result)


def _format_server_query(init_result: Any, tools_result: Any) -> dict[str, Any]:
    return {
        "server_info": init_result.serverInfo,
        "instructions": init_result.instructions or "",
        "tools": [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.inputSchema,
            }
            for t in tools_result.tools
        ],
    }


async def _call_server_tool_async(
    name: str,
    arguments: dict[str, object],
) -> dict[str, Any]:
    async with _mcp_session() as session:
        call_result = await session.call_tool(name, arguments)
        if call_result.isError:
            raise RuntimeError(
                "Tool {:s} returned error: {!r}".format(name, call_result.content)
            )
        text = call_result.content[0].text  # type: ignore[attr-defined]
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise TypeError("Expected JSON object from tool {:s}".format(name))
        return payload


def query_server() -> dict[str, Any]:
    """
    Connect to the MCP server and return tool metadata.
    """
    return asyncio.run(_query_server_async())


def call_server_tool(name: str, arguments: dict[str, object]) -> dict[str, Any]:
    """
    Call an MCP tool and return the JSON payload from the first text block.
    """
    return asyncio.run(_call_server_tool_async(name, arguments))
