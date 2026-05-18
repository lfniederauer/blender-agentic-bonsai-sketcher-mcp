# SPDX-FileCopyrightText: 2026 Blender Authors
# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
MCP server for Blender.

Provides tools for LLM's, connecting to Blender via a bridge-server.
All tools send code to the add-on to run.
"""

__all__ = (
    "create_mcp_server",
    "configure_http_transport",
    "main",
)

import argparse
import importlib
import os
import pkgutil
from collections.abc import Callable

import yaml
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from starlette.requests import Request
from starlette.responses import JSONResponse

# NOTE(@ideasman42): this was written to support LLAMA-C++'s Web UI,
# which is one of the nicer ways to run this locally.
# It is not full HTTP support because there looks to be many options for this protocol.
# This could be disabled if it no longer serves its purpose - as most agents wont use STDIO.
_USE_HTTP_SUPPORT = True

_TRANSPORTS = ("stdio", *(("http",) if _USE_HTTP_SUPPORT else ()))


def create_mcp_server() -> FastMCP:
    # Load prompts.
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    with open(os.path.join(data_dir, "prompts.yml"), encoding="utf-8") as fh:
        prompts = yaml.safe_load(fh)

    mcp = FastMCP("blender-mcp", instructions=str(prompts["initial_instructions"]))

    # Auto-discover and register all tools (they are never un-registered).
    import blmcp.tools as tools_pkg

    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.endswith("_toolcode") or modname.startswith("_template_"):
            continue
        mod = importlib.import_module("blmcp.tools.{:s}".format(modname))
        if hasattr(mod, "register"):
            mod.register(mcp)

    @mcp.custom_route("/health", methods=["GET"])
    async def _health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy", "service": "blender-mcp"})

    return mcp


def configure_http_transport(mcp: FastMCP, host: str, port: int) -> str:
    # pylint: disable-next=import-error,no-name-in-module
    from mcp.server.fastmcp.server import TransportSecuritySettings  # type: ignore[attr-defined]
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware

    transport = "streamable-http"
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.streamable_http_path = "/"
    mcp.settings.stateless_http = True
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )

    # Add CORS middleware so browser-based clients can connect without preflight failures.
    orig_streamable_app: Callable[[], Starlette] = mcp.streamable_http_app

    def _app_with_cors() -> Starlette:
        app = orig_streamable_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

    mcp.streamable_http_app = _app_with_cors  # type: ignore[method-assign]
    return transport


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP server for Blender.")
    parser.add_argument(
        "--transport", "-t",
        choices=_TRANSPORTS,
        default="stdio",
        help="Transport protocol (default: stdio).",
    )
    if _USE_HTTP_SUPPORT:
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind to for HTTP transports (default: 127.0.0.1).",
        )
        parser.add_argument(
            "--port", "-p",
            type=int,
            default=8000,
            help="Port to bind to for HTTP transports (default: 8000).",
        )
    args = parser.parse_args()

    mcp = create_mcp_server()
    transport = args.transport
    if _USE_HTTP_SUPPORT and transport == "http":
        transport = configure_http_transport(mcp=mcp, host=args.host, port=args.port)

    mcp.run(transport=transport)
    return 0
