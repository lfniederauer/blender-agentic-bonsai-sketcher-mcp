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
            title="BIM Assign Spatial Container",
            destructiveHint=True,
        )
    )
    def bim_assign_spatial(element_ids: list[int], container_id: int) -> dict[str, object]:
        """
        Assign IFC elements to a spatial container (storey/building/site).
        """
        element_ids_json = json.dumps(element_ids)
        container_id_int = int(container_id)
        code = build_bim_tool_code(
            f"""
element_ids = {element_ids_json}
container_id = {container_id_int}
container = model.by_id(container_id)
if container is None:
    result = {{"status": "error", "error": f"Container #{{container_id}} not found."}}
else:
    elements = []
    missing = []
    for eid in element_ids:
        ent = model.by_id(int(eid))
        if ent is None:
            missing.append(int(eid))
        else:
            elements.append(ent)
    if not elements:
        result = {{"status": "error", "error": "No valid elements found for assignment.", "missing": missing}}
    else:
        try:
            tool.Ifc.run("spatial.assign_container", products=elements, relating_structure=container)
            try:
                tool.Ifc.rebuild_element_maps()
            except Exception:
                pass
            result = {{
                "status": "ok",
                "container_id": container_id,
                "assigned_count": len(elements),
                "missing": missing,
            }}
        except Exception as ex:
            result = {{"status": "error", "error": f"Spatial assignment failed: {{type(ex).__name__}}: {{ex}}"}}
""",
            with_tool=True,
        )
        return send_code(code, strict_json=True)
