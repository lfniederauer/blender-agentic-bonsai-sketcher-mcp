# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Synchronous MCP client over streamable HTTP (Docker blender-mcp service).
"""

__all__ = (
    "MCPHttpClient",
)

import asyncio
from typing import Any, Self

from mcp.types import TextContent

from tests.utils.mcp_connect import _mcp_session


class MCPHttpClient:
    """
    Synchronous wrapper around streamable HTTP MCP for Blender integration tests.
    """

    def __init__(self, url: str) -> None:
        self._url = url if url.endswith("/") else url + "/"
        self._session_cm = None
        self._session = None
        self._loop = asyncio.new_event_loop()

    def initialize(self) -> dict[str, Any]:
        async def _init() -> dict[str, Any]:
            self._session_cm = _mcp_session()
            self._session = await self._session_cm.__aenter__()
            return {}

        return self._loop.run_until_complete(_init())

    def list_tools(self) -> list[str]:
        async def _list() -> list[str]:
            assert self._session is not None
            result = await self._session.list_tools()
            return [t.name for t in result.tools]

        return self._loop.run_until_complete(_list())

    def call_tool(
        self,
        name: str,
        arguments: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        async def _call() -> dict[str, Any]:
            assert self._session is not None
            params: dict[str, object] = {"name": name}
            if arguments is not None:
                params["arguments"] = arguments
            call_result = await self._session.call_tool(name, arguments or {})
            content: list[dict[str, object]] = []
            for block in call_result.content:
                if isinstance(block, TextContent):
                    content.append({"type": "text", "text": block.text})
                elif hasattr(block, "type"):
                    content.append({"type": block.type, "data": getattr(block, "data", "")})
                else:
                    content.append({"type": "text", "text": str(block)})
            return {
                "content": content,
                "isError": bool(call_result.isError),
            }

        return self._loop.run_until_complete(_call())

    def close(self) -> None:
        if self._session_cm is not None:
            self._loop.run_until_complete(self._session_cm.__aexit__(None, None, None))
            self._session_cm = None
            self._session = None
        self._loop.close()

    def __enter__(self) -> Self:
        self.initialize()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
