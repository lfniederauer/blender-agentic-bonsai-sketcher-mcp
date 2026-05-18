# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

from blmcp.tools_helpers.bonsai_helpers import build_bim_tool_code
from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_CODE = build_bim_tool_code(
    """
by_type = {}
for ent in model:
    ent_type = ent.is_a()
    by_type[ent_type] = by_type.get(ent_type, 0) + 1
top_types = sorted(by_type.items(), key=lambda kv: kv[1], reverse=True)[:30]
projects = model.by_type("IfcProject")
units = model.by_type("IfcUnitAssignment")
result = {
    "status": "ok",
    "ifc_path": IfcStore.path or "",
    "schema": model.schema,
    "entity_count": sum(by_type.values()),
    "project_count": len(projects),
    "projects": [
        {
            "id": int(proj.id()),
            "name": getattr(proj, "Name", None),
            "long_name": getattr(proj, "LongName", None),
            "description": getattr(proj, "Description", None),
        }
        for proj in projects
    ],
    "unit_assignment_count": len(units),
    "top_entity_types": [{"type": item_type, "count": count} for item_type, count in top_types],
}
"""
)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Summary",
            readOnlyHint=True,
        )
    )
    def bim_summary() -> dict[str, object]:
        """
        Return IFC summary: schema, project info and top entity counts.
        """
        return send_code(_CODE, strict_json=True)
