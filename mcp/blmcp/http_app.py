# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
FastAPI application wrapper for the Blender MCP server.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from blmcp import configure_http_transport, create_mcp_server

_mcp = create_mcp_server()
configure_http_transport(mcp=_mcp, host="0.0.0.0", port=5001)

app = FastAPI(
    title="blender-agentic-bonsai-sketcher-mcp",
    version="1.0.0",
    description="HTTP wrapper for Blender agentic Bonsai / CAD Sketcher MCP server.",
)
app.mount("/", _mcp.streamable_http_app())


@app.get("/health")
async def health() -> JSONResponse:
    """
    Health-check endpoint for compose deployments.
    """
    return JSONResponse({"status": "ok"})
