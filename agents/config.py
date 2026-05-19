# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for BIM Google ADK agents."""
from __future__ import annotations

import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    """Settings loaded from environment and optional .env file."""

    # Matches mcp/docker-compose.yml default HTTP endpoint.
    blender_mcp_http_url: str = "http://127.0.0.1:8050/"
    mcp_request_timeout_seconds: float = 45.0

    adk_model: str = "gemini-3.1-flash-lite"
    adk_model_coordinator: str | None = None
    adk_model_researcher: str | None = None
    adk_model_geometry: str | None = None
    adk_model_appearance: str | None = None
    adk_model_properties: str | None = None
    adk_model_costs: str | None = None
    adk_model_inspector: str | None = None

    # When true, ADK LoggingPlugin + per-event trace lines (CLI stderr / NDJSON type=trace).
    adk_trace: bool = False

    model_config = {"env_file": ".env", "extra": "ignore", "env_prefix": ""}

    @field_validator("adk_trace", mode="before")
    @classmethod
    def _adk_trace_from_env(cls, v: bool) -> bool:
        if v:
            return True
        raw = os.environ.get("ADK_TRACE", "").strip().lower()
        return raw in ("1", "true", "yes", "on")

    @field_validator("blender_mcp_http_url", mode="before")
    @classmethod
    def _mcp_http_url_from_env(cls, v: str) -> str:
        explicit_url = os.environ.get("BLENDER_MCP_HTTP_URL") or os.environ.get("MCP_HTTP_URL")
        if explicit_url:
            return explicit_url
        http_port = os.environ.get("BLENDER_MCP_HTTP_PORT")
        if http_port:
            return f"http://127.0.0.1:{http_port}/"
        return v

