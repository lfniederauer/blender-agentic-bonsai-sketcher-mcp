# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
CLI and ADK web entrypoint for the BIM multi-agent coordinator.

**HTTP (Docker / clients):** ``agents.http_app`` exposes ``POST /api/agent/chat``
with the same NDJSON stream as :func:`iter_agent_chat_ndjson`.

Usage:
    PYTHONPATH=. python -m agents.main "bim_status and summarize the scene"

For ADK web UI:
    adk web agents/main.py
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from agents.agent import create_agent
from agents.runner import iter_agent_chat_ndjson, run_async

__all__ = ["iter_agent_chat_ndjson", "main", "root_agent", "run_agent_query"]

# Required by ADK web runner.
root_agent = create_agent()


async def run_agent_query(user_message: str, *, trace: bool = False) -> str:
    """Run one stateless BIM agent turn and return full text."""
    return await run_async(user_message, trace=trace)


async def _main_async(query: str, *, trace: bool = False) -> None:
    result = await run_agent_query(query, trace=trace)
    print(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the BIM Google ADK coordinator (Blender MCP + specialist sub-agents).",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print ADK coordination trace to stderr (agent/tool/function_call events).",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="User query (if omitted, reads from stdin).",
    )
    args = parser.parse_args()
    query = args.query
    if query is None:
        query = sys.stdin.read().strip()
    if not query:
        parser.error("Provide a query as argument or via stdin.")
    asyncio.run(_main_async(query, trace=args.trace))


if __name__ == "__main__":
    main()

