# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Serialize Google ADK events for CLI trace and NDJSON streaming."""

from __future__ import annotations

import json
from typing import Any


def _truncate(value: str, max_len: int = 400) -> str:
    text = value.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def serialize_event(event: Any) -> dict[str, Any]:
    """Turn an ADK Event into a JSON-safe dict for trace output."""
    payload: dict[str, Any] = {
        "id": getattr(event, "id", None),
        "author": getattr(event, "author", None),
        "branch": getattr(event, "branch", None),
    }
    if hasattr(event, "is_final_response"):
        payload["final"] = bool(event.is_final_response())

    if hasattr(event, "get_function_calls"):
        calls = event.get_function_calls()
        if calls:
            payload["function_calls"] = [
                {
                    "name": fc.name,
                    "id": getattr(fc, "id", None),
                    "args": dict(fc.args) if getattr(fc, "args", None) else None,
                }
                for fc in calls
            ]

    if hasattr(event, "get_function_responses"):
        responses = event.get_function_responses()
        if responses:
            payload["function_responses"] = [
                {
                    "name": fr.name,
                    "id": getattr(fr, "id", None),
                    "response": fr.response,
                }
                for fr in responses
            ]

    content = getattr(event, "content", None)
    if content and getattr(content, "parts", None):
        parts_out: list[dict[str, Any]] = []
        for part in content.parts:
            if getattr(part, "text", None):
                parts_out.append({"text": _truncate(part.text)})
            elif getattr(part, "function_call", None):
                fc = part.function_call
                parts_out.append(
                    {
                        "function_call": {
                            "name": fc.name,
                            "id": getattr(fc, "id", None),
                        }
                    }
                )
            elif getattr(part, "function_response", None):
                fr = part.function_response
                parts_out.append(
                    {
                        "function_response": {
                            "name": fr.name,
                            "id": getattr(fr, "id", None),
                        }
                    }
                )
        if parts_out:
            payload["parts"] = parts_out

    return payload


def format_event_line(event_dict: dict[str, Any]) -> str:
    """Single-line human trace for stderr."""
    author = event_dict.get("author") or "?"
    branch = event_dict.get("branch")
    prefix = f"[{author}]"
    if branch:
        prefix += f" ({branch})"

    if event_dict.get("function_calls"):
        names = [c["name"] for c in event_dict["function_calls"]]
        return f"{prefix} -> call {', '.join(names)}"

    if event_dict.get("function_responses"):
        names = [r["name"] for r in event_dict["function_responses"]]
        return f"{prefix} <- response {', '.join(names)}"

    for part in event_dict.get("parts") or []:
        if "text" in part:
            return f"{prefix} text: {part['text']}"

    if event_dict.get("final"):
        return f"{prefix} (final)"
    return f"{prefix} event"


def dumps_trace_event(event: Any) -> str:
    return json.dumps({"type": "trace", "event": serialize_event(event)}, ensure_ascii=False)
