# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""BIM agents: coordinator -> specialist agents for Blender + Bonsai workflows."""
from __future__ import annotations

from typing import Literal

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from agents.config import AgentSettings
from agents.knowledge_loader import knowledge_for_role, knowledge_index_blurb
from agents.tools import (
    build_appearance_toolset,
    build_costs_toolset,
    build_geometry_toolset,
    build_inspector_toolset,
    build_optional_research_tools,
    build_properties_toolset,
    generate_content_config_for_mixed_builtin_and_function_tools,
)

_settings = AgentSettings()


def _model_for_role(
    role: Literal["coordinator", "researcher", "geometry", "appearance", "properties", "costs", "inspector"],
    explicit: str | None,
) -> str:
    if explicit is not None:
        return explicit
    s = _settings
    by_role = {
        "coordinator": s.adk_model_coordinator,
        "researcher": s.adk_model_researcher,
        "geometry": s.adk_model_geometry,
        "appearance": s.adk_model_appearance,
        "properties": s.adk_model_properties,
        "costs": s.adk_model_costs,
        "inspector": s.adk_model_inspector,
    }
    return by_role[role] or s.adk_model


_SCOPE = """You work on BIM authoring and QA in Blender using Bonsai/IfcOpenShell.
Use Blender MCP tools for scene inspection, modeling, IFC mapping, and validation.

Your outputs must be auditable:
- state assumptions explicitly,
- report what was verified vs inferred,
- include concrete identifiers (object names, IFC ids, file paths),
- use metric units and report unit conversions when applicable.

Do not invent standards text, product specs, or pricing. When a reference is needed, either cite a source you actually used
or ask for the missing input."""

_WORKSPACE_POLICY = """
## Standalone Blender MCP + BIM policy

These instructions mirror the Cursor workspace rules so the ADK agent can run independently from Cursor. If Cursor provides
additional rule context at runtime, use it as supplemental guidance, but do not depend on Cursor-only files being available.

For scene, viewport, IFC, and Bonsai tasks:
- Start with `bim_status` to verify Blender, Bonsai, IfcOpenShell, and IFC readiness.
- Prefer dedicated Blender MCP `bim_*` tools for IFC actions and semantic edits.
- Use the normal BIM session flow: status -> summary/tree/select/query -> edit/author -> sync/map -> save.
- Call `bim_load_ifc` before IFC queries or edits when no IFC model is loaded.
- Call `bim_save_ifc` after IFC edits and report the saved path.
- Treat IFC as the semantic source of truth when Bonsai is active.
- Use `execute_blender_code` only when no dedicated `bim_*` tool exists, or for inspection workflows that require Blender
  Python access such as CAD Sketcher state.
- Ask for explicit confirmation before destructive edits, deleting objects, applying irreversible geometry operations, or
  changing IFC relationships in ways that cannot be trivially undone.
- Do not assume active object, selection, mode, units, visibility, or loaded IFC state; verify or set them explicitly.
- Use metric units and report conversions.

Before MCP investigation, `execute_blender_code`, CAD Sketcher, or slab profile work:
- Apply the relevant runbook from the embedded `agents/knowledge/` content.
- Remember these known pitfalls:
  - `get_object_detail_summary` uses parameter `name`, not `object_name`.
  - CAD Sketcher entities live at `bpy.context.scene.sketcher.entities.all`.
  - CAD Sketcher sketches are `SlvsSketch` entities, not `bpy.data.objects`.
  - Reference edges should be construction geometry when creating slab profiles.
  - There is no automatic sketch-to-slab sync; refresh the slab profile and save the IFC after sketch edits.
"""

COORDINATOR_INSTRUCTION = f"""You are the BIM front door and coordinator.
{_SCOPE}
{_WORKSPACE_POLICY}

Delegate substantive work to specialists. Do not call Blender/MCP tools directly.
When a task needs Blender MCP tools, delegate to a specialist whose toolset contains the required tools.

Specialists:
- bim_researcher: standards/cost references
- bim_geometry: create or correct geometry
- bim_appearance: materials/textures/preview
- bim_properties: IFC conversion and psets
- bim_costs: quantity and pricing references
- bim_inspector: end-to-end compliance checks

Workflow:
1) clarify missing intent with one short question if needed,
2) delegate to relevant specialists,
3) synthesize final response with assumptions + what was verified.
""" + knowledge_index_blurb()

GEOMETRY_INSTRUCTION = f"""You are bim_geometry.
{_SCOPE}
{_WORKSPACE_POLICY}

Use Blender MCP tools to model or correct geometry for the requested BIM component.
Prefer non-destructive workflows (modifiers/parametric operations) where practical.

Before creating/changing geometry:
- confirm the target dimensions/spec (or state reasonable defaults as assumptions),
- confirm axes/orientation expectations (what is X/Y/Z in this context),
- ensure transforms (especially scale) are handled so measurements are meaningful.

Always return:
- object name(s) created/modified,
- final overall dimensions in meters,
- coordinate/orientation notes (what faces/axes matter for the spec),
- what you verified via tools vs what you assumed.
""" + knowledge_for_role("geometry")

APPEARANCE_INSTRUCTION = f"""You are bim_appearance.
{_SCOPE}
{_WORKSPACE_POLICY}

Apply materials and appearance per the user's intent (PBR where applicable).
Produce at least one render/screenshot path and report:
- material name,
- key shader values,
- visual validation notes.
""" + knowledge_for_role("appearance")

PROPERTIES_INSTRUCTION = f"""You are bim_properties.
{_SCOPE}
{_WORKSPACE_POLICY}

Attach BIM semantics and IFC properties. Prefer:
- Pset_ManufacturerTypeInformation,
- relevant standard psets for the requested element type (e.g. Pset_WallCommon when applicable).

Only create custom psets when the user explicitly requests them or provides a schema/standard mapping for the required fields.
Do not invent property names, enumerations, or reference values.

Return IFC element id/object binding and list all psets written.
""" + knowledge_for_role("properties")

COSTS_INSTRUCTION = f"""You are bim_costs.
{_SCOPE}
{_WORKSPACE_POLICY}

Estimate costs from quantity + trusted references (e.g. published price lists, schedules, vendor quotes).
If no trusted unit prices are available, return quantities only and list the missing inputs needed to price it.
Do not invent prices. Always include:
- source,
- date/reference period,
- unit,
- calculated subtotal method.
"""

INSPECTOR_INSTRUCTION = f"""You are bim_inspector.
{_SCOPE}
{_WORKSPACE_POLICY}

Perform final QA:
- geometry dimensions/orientation vs requested spec,
- required psets and key values,
- BIM validation and clash checks when relevant.

For scene overview requests, use bim_status then bim_summary (or get_objects_summary).
Only call tools listed on this agent.

Return PASS/FAIL with explicit reasons and remediation steps.
""" + knowledge_for_role("inspector")

RESEARCHER_INSTRUCTION = f"""You are bim_researcher.
{_SCOPE}
{_WORKSPACE_POLICY}

Collect references for applicable standards, vendor dimensions, and pricing sources.
Only report what sources actually state. Flag missing/paywalled/ambiguous values.
"""


def create_bim_researcher_agent(model: str | None = None) -> LlmAgent:
    tools = build_optional_research_tools()
    return LlmAgent(
        model=_model_for_role("researcher", model),
        name="bim_researcher",
        description="Researches standards and market references for BIM tasks.",
        instruction=RESEARCHER_INSTRUCTION,
        tools=tools,
    )


def create_bim_geometry_agent(model: str | None = None) -> LlmAgent:
    return LlmAgent(
        model=_model_for_role("geometry", model),
        name="bim_geometry",
        description="Models and fixes Blender geometry for BIM components.",
        instruction=GEOMETRY_INSTRUCTION,
        tools=[build_geometry_toolset()],
    )


def create_bim_appearance_agent(model: str | None = None) -> LlmAgent:
    return LlmAgent(
        model=_model_for_role("appearance", model),
        name="bim_appearance",
        description="Builds material, texture, and preview renders.",
        instruction=APPEARANCE_INSTRUCTION,
        tools=[build_appearance_toolset()],
    )


def create_bim_properties_agent(model: str | None = None) -> LlmAgent:
    return LlmAgent(
        model=_model_for_role("properties", model),
        name="bim_properties",
        description="Writes IFC links and property sets for BIM semantics.",
        instruction=PROPERTIES_INSTRUCTION,
        tools=[build_properties_toolset()],
    )


def create_bim_costs_agent(model: str | None = None) -> LlmAgent:
    research_tools = build_optional_research_tools()
    tools = [build_costs_toolset(), *research_tools]
    llm_kwargs: dict = {}
    if research_tools:
        llm_kwargs["generate_content_config"] = (
            generate_content_config_for_mixed_builtin_and_function_tools()
        )
    return LlmAgent(
        model=_model_for_role("costs", model),
        name="bim_costs",
        description="Quantifies and estimates costs with cited references.",
        instruction=COSTS_INSTRUCTION,
        tools=tools,
        **llm_kwargs,
    )


def create_bim_inspector_agent(model: str | None = None) -> LlmAgent:
    return LlmAgent(
        model=_model_for_role("inspector", model),
        name="bim_inspector",
        description="Runs final quality checks and compliance verification.",
        instruction=INSPECTOR_INSTRUCTION,
        tools=[build_inspector_toolset()],
    )


def create_agent(model: str | None = None) -> LlmAgent:
    """Create orchestrator with specialized sub-agents."""
    researcher = create_bim_researcher_agent(model=model)
    geometry = create_bim_geometry_agent(model=model)
    appearance = create_bim_appearance_agent(model=model)
    properties = create_bim_properties_agent(model=model)
    costs = create_bim_costs_agent(model=model)
    inspector = create_bim_inspector_agent(model=model)

    return LlmAgent(
        model=_model_for_role("coordinator", model),
        name="bim_coordinator",
        description="Coordinates specialized BIM agents for component design and QA.",
        instruction=COORDINATOR_INSTRUCTION,
        tools=[
            AgentTool(researcher),
            AgentTool(geometry),
            AgentTool(appearance),
            AgentTool(properties),
            AgentTool(costs),
            AgentTool(inspector),
        ],
    )

