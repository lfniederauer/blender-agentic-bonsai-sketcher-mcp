# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
FastAPI app: BIM ADK coordinator chat (NDJSON stream) for Docker and HTTP clients.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="BIM Agent Runner",
    description=(
        "HTTP API for the Google ADK BIM multi-agent coordinator. "
        "Delegates to Blender MCP tools via the streamable HTTP MCP service."
    ),
    version="1.0.0",
)


class AgentChatBody(BaseModel):
    message: str | None = None
    messages: list[str] = Field(default_factory=list)
    session_id: str | None = None
    device_id: str | None = None


def _agent_user_text(body: AgentChatBody) -> str:
    if body.message and body.message.strip():
        return body.message.strip()
    for message in reversed(body.messages):
        if isinstance(message, str) and message.strip():
            return message.strip()
    return ""


@app.get("/health")
@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "bim-agent-runner"})


@app.post("/agent/chat")
@app.post("/api/agent/chat")
async def agent_chat(body: AgentChatBody):
    """
    Run one BIM coordinator turn. Streams newline-delimited JSON:
    {"type":"content","text":"..."}, then {"type":"final","session_id":"..."}.
    """
    text = _agent_user_text(body)
    if not text:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide non-empty message or messages[]"},
        )

    from agents.runner import iter_agent_chat_ndjson

    async def ndjson_bytes():
        async for line in iter_agent_chat_ndjson(text):
            yield line.encode("utf-8")

    return StreamingResponse(
        ndjson_bytes(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
