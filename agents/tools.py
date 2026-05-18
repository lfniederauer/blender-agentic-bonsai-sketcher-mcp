# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tool builders for BIM ADK agents (Blender MCP + optional web research)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.genai import types

from agents.config import AgentSettings

if TYPE_CHECKING:
    from google.adk.tools import BaseTool, BaseToolset

_settings = AgentSettings()

# Geometry and model assembly
GEOMETRY_TOOLS: tuple[str, ...] = (
    "execute_blender_code",
    "get_objects_summary",
    "get_object_detail_summary",
    "bim_status",
    "bim_load_ifc",
    "bim_summary",
    "bim_tree",
    "bim_select",
    "bim_execute_bonsai_op",
    "bim_save_ifc",
    "jump_to_view3d_object_by_name",
)

# Material/appearance/visual QA
APPEARANCE_TOOLS: tuple[str, ...] = (
    "execute_blender_code",
    "get_screenshot_of_area_as_image",
    "render_thumbnail_to_path",
    "jump_to_view3d_object_by_name",
)

# IFC and BIM semantics
PROPERTIES_TOOLS: tuple[str, ...] = (
    "bim_status",
    "bim_load_ifc",
    "bim_add_pset",
    "bim_create_element",
    "bim_info",
    "bim_edit",
    "bim_object_to_ifc",
    "bim_assign_spatial",
    "bim_execute_bonsai_op",
    "bim_save_ifc",
    "execute_blender_code",
)

# Cost estimation support
COSTS_TOOLS: tuple[str, ...] = (
    "bim_status",
    "bim_quantify",
)

# End-to-end quality checks
INSPECTOR_TOOLS: tuple[str, ...] = (
    "bim_status",
    "bim_load_ifc",
    "bim_summary",
    "bim_tree",
    "get_objects_summary",
    "bim_validate",
    "bim_info",
    "bim_clash",
    "get_object_detail_summary",
    "get_screenshot_of_area_as_image",
)


def build_blender_toolset(tool_filter: list[str] | None = None) -> "BaseToolset":
    """Build Blender MCP toolset over streamable HTTP."""
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=_settings.blender_mcp_http_url,
            timeout=_settings.mcp_request_timeout_seconds,
        ),
        tool_filter=tool_filter,
    )


def build_geometry_toolset() -> "BaseToolset":
    return build_blender_toolset(tool_filter=list(GEOMETRY_TOOLS))


def build_appearance_toolset() -> "BaseToolset":
    return build_blender_toolset(tool_filter=list(APPEARANCE_TOOLS))


def build_properties_toolset() -> "BaseToolset":
    return build_blender_toolset(tool_filter=list(PROPERTIES_TOOLS))


def build_costs_toolset() -> "BaseToolset":
    return build_blender_toolset(tool_filter=list(COSTS_TOOLS))


def build_inspector_toolset() -> "BaseToolset":
    return build_blender_toolset(tool_filter=list(INSPECTOR_TOOLS))


def generate_content_config_for_mixed_builtin_and_function_tools() -> types.GenerateContentConfig:
    """Gemini requires this when an agent mixes server-side tools with function calling."""
    return types.GenerateContentConfig(
        tool_config=types.ToolConfig(include_server_side_tool_invocations=True),
    )


def build_optional_research_tools() -> list["BaseTool"]:
    """
    Return optional web-search tool(s) when available.

    Kept optional so the agent package can import even when ADK/provider extras are
    not installed in the local environment yet.
    """
    try:
        from google.adk.tools import google_search  # type: ignore

        return [google_search]  # pragma: no cover - runtime availability dependent
    except Exception:
        # Backward compatibility with older ADK module layouts.
        try:
            from google.adk.tools.google_search_tool import google_search  # type: ignore

            return [google_search]  # pragma: no cover - runtime availability dependent
        except Exception:
            return []

