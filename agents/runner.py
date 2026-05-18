# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""In-memory runner helpers for BIM ADK agents."""

from __future__ import annotations

import json
import sys
import uuid
from collections.abc import AsyncIterator, Callable

from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.agent import create_agent
from agents.config import AgentSettings
from agents.event_trace import dumps_trace_event, format_event_line, serialize_event

_settings = AgentSettings()


def _runner_plugins():
    if not _settings.adk_trace:
        return None
    try:
        from google.adk.plugins.logging_plugin import LoggingPlugin

        return [LoggingPlugin(name="bim_trace")]
    except ImportError:
        return None


def get_runner(agent=None, *, trace: bool | None = None):
    """Return an InMemoryRunner with default BIM coordinator agent."""
    if agent is None:
        agent = create_agent()
    plugins = _runner_plugins() if (trace if trace is not None else _settings.adk_trace) else None
    return InMemoryRunner(agent=agent, plugins=plugins)


async def _run_events(
    user_message: str,
    agent=None,
    *,
    trace: bool | None = None,
    on_event: Callable[[object], None] | None = None,
):
    """Yield ADK events for one user turn."""
    runner = get_runner(agent=agent, trace=trace)
    app_name = runner.app_name
    user_id = "default"
    session_id = f"run-{uuid.uuid4().hex[:12]}"

    session_service = runner.session_service
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    content = types.Content(role="user", parts=[types.Part(text=user_message)])
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=content,
    ):
        if on_event is not None:
            on_event(event)
        yield event


async def run_async(
    user_message: str,
    agent=None,
    *,
    trace: bool | None = None,
    trace_stream: Callable[[str], None] | None = None,
) -> str:
    """Run agent once and return final text output."""
    emit = trace_stream or (lambda line: print(line, file=sys.stderr, flush=True))
    use_trace = trace if trace is not None else _settings.adk_trace

    final_text: list[str] = []
    async for event in _run_events(user_message, agent=agent, trace=use_trace):
        if use_trace:
            emit(format_event_line(serialize_event(event)))
        if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_text.append(part.text)
    return "\n".join(final_text) if final_text else ""


async def iter_agent_chat_ndjson(
    user_message: str,
    agent=None,
    *,
    trace: bool | None = None,
) -> AsyncIterator[str]:
    """Stream agent output as NDJSON events."""
    use_trace = trace if trace is not None else _settings.adk_trace
    session_id_holder: list[str] = []

    try:
        runner = get_runner(agent=agent, trace=use_trace)
        app_name = runner.app_name
        user_id = "default"
        session_id = f"run-{uuid.uuid4().hex[:12]}"
        session_id_holder.append(session_id)
        session_service = runner.session_service
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )

        content = types.Content(role="user", parts=[types.Part(text=user_message)])
        async for event in runner.run_async(
            session_id=session_id,
            user_id=user_id,
            new_message=content,
        ):
            if use_trace:
                yield dumps_trace_event(event) + "\n"
            if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield json.dumps({"type": "content", "text": part.text}, ensure_ascii=False) + "\n"
        yield json.dumps({"type": "final", "session_id": session_id}) + "\n"
    except Exception as exc:  # noqa: BLE001
        yield json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False) + "\n"
        sid = session_id_holder[0] if session_id_holder else None
        yield json.dumps({"type": "final", "session_id": sid}) + "\n"
