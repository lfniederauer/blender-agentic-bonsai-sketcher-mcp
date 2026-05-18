# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

import json

from blmcp.tools_helpers.bonsai_helpers import build_bim_tool_code
from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Object To IFC",
            readOnlyHint=True,
        )
    )
    def bim_object_to_ifc(object_name: str) -> dict[str, object]:
        """
        Resolve a Blender object to its linked IFC entity.
        """
        object_name_json = json.dumps(object_name)
        code = build_bim_tool_code(
            f"""
object_name = {object_name_json}
obj = bpy.data.objects.get(object_name)
if obj is None:
    result = {{"status": "error", "error": f"Object '{{object_name}}' not found."}}
else:
    try:
        ent = tool.Ifc.get_entity(obj)
    except Exception as ex:
        result = {{"status": "error", "error": f"Failed to resolve IFC entity: {{type(ex).__name__}}: {{ex}}"}}
    else:
        if ent is None:
            result = {{"status": "ok", "object_name": object_name, "ifc_entity": None}}
        else:
            result = {{
                "status": "ok",
                "object_name": object_name,
                "ifc_entity": {{
                    "id": int(ent.id()),
                    "type": ent.is_a(),
                    "guid": getattr(ent, "GlobalId", None),
                    "name": getattr(ent, "Name", None),
                }},
            }}
""",
            require_ifc=False,
            with_bpy=True,
            with_tool=True,
        )
        return send_code(code, strict_json=True)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM IFC To Object",
            readOnlyHint=True,
        )
    )
    def bim_ifc_to_object(element_id: int) -> dict[str, object]:
        """
        Resolve an IFC STEP id to its linked Blender object.
        """
        code = build_bim_tool_code(
            f"""
element_id = {int(element_id)}
ent = model.by_id(element_id)
if ent is None:
    result = {{"status": "error", "error": f"Element #{{element_id}} not found."}}
else:
    try:
        obj = tool.Ifc.get_object(ent)
        result = {{
            "status": "ok",
            "element_id": element_id,
            "object_name": obj.name if obj else None,
        }}
    except Exception as ex:
        result = {{"status": "error", "error": f"Failed to resolve object: {{type(ex).__name__}}: {{ex}}"}}
""",
            with_tool=True,
        )
        return send_code(code, strict_json=True)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Sync Selection",
            destructiveHint=True,
        )
    )
    def bim_sync_selection(
        direction: str = "blender_to_ifc",
        element_ids: list[int] | None = None,
    ) -> dict[str, object]:
        """
        Sync selection between Blender objects and IFC entities.

        direction: blender_to_ifc | ifc_to_blender
        element_ids: optional IFC ids to select when syncing ifc_to_blender
        """
        direction_json = json.dumps(direction)
        element_ids_json = json.dumps(element_ids)
        code = build_bim_tool_code(
            f"""
direction = {direction_json}
element_ids = {element_ids_json}
model = IfcStore.get_file()
if direction == "blender_to_ifc":
    out = []
    for obj in bpy.context.selected_objects:
        try:
            ent = tool.Ifc.get_entity(obj)
        except Exception:
            ent = None
        if ent is not None:
            out.append({{"object": obj.name, "id": int(ent.id()), "type": ent.is_a(), "guid": getattr(ent, "GlobalId", None)}})
    result = {{"status": "ok", "direction": direction, "selected_ifc_elements": out}}
elif direction == "ifc_to_blender":
    if model is None:
        result = {{"status": "error", "error": "No IFC loaded in Bonsai."}}
    else:
        targets = []
        if element_ids:
            targets = [model.by_id(int(eid)) for eid in element_ids]
        else:
            active = bpy.context.view_layer.objects.active
            ent = None
            if active is not None:
                try:
                    ent = tool.Ifc.get_entity(active)
                except Exception:
                    ent = None
            if ent is not None:
                targets = [ent]
        targets = [item for item in targets if item is not None]
        if not targets:
            result = {{"status": "error", "error": "No IFC elements resolved for selection sync."}}
        else:
            try:
                for item in bpy.context.selected_objects:
                    item.select_set(False)
                active_obj = None
                resolved = []
                for ent in targets:
                    obj = tool.Ifc.get_object(ent)
                    if obj is not None:
                        obj.select_set(True)
                        if active_obj is None:
                            active_obj = obj
                    resolved.append({{"element_id": int(ent.id()), "object_name": obj.name if obj else None}})
                if active_obj is not None:
                    bpy.context.view_layer.objects.active = active_obj
                result = {{"status": "ok", "direction": direction, "resolved": resolved, "active_object": active_obj.name if active_obj else None}}
            except Exception as ex:
                result = {{"status": "error", "error": f"Selection sync failed: {{type(ex).__name__}}: {{ex}}"}}
else:
    result = {{"status": "error", "error": "direction must be 'blender_to_ifc' or 'ifc_to_blender'."}}
""",
            require_ifc=False,
            with_bpy=True,
            with_tool=True,
        )
        return send_code(code, strict_json=True)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Highlight Elements",
            destructiveHint=True,
        )
    )
    def bim_highlight_elements(element_ids: list[int]) -> dict[str, object]:
        """
        Highlight IFC-linked objects by selecting and activating them in Blender.
        """
        ids_json = json.dumps(element_ids)
        code = build_bim_tool_code(
            f"""
element_ids = {ids_json}
resolved = []
for item in bpy.context.selected_objects:
    item.select_set(False)
active_obj = None
for eid in element_ids:
    ent = model.by_id(int(eid))
    if ent is None:
        resolved.append({{"element_id": int(eid), "object_name": None, "found": False}})
        continue
    obj = tool.Ifc.get_object(ent)
    if obj is not None:
        obj.select_set(True)
        if active_obj is None:
            active_obj = obj
    resolved.append({{"element_id": int(eid), "object_name": obj.name if obj else None, "found": obj is not None}})
if active_obj is not None:
    bpy.context.view_layer.objects.active = active_obj
result = {{
    "status": "ok",
    "requested": len(element_ids),
    "resolved": resolved,
    "active_object": active_obj.name if active_obj else None,
}}
""",
            with_bpy=True,
            with_tool=True,
        )
        return send_code(code, strict_json=True)
