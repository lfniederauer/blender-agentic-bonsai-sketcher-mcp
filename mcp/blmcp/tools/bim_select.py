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
            title="BIM Select",
            readOnlyHint=True,
        )
    )
    def bim_select(query: str) -> dict[str, object]:
        """
        Query IFC elements using IfcOpenShell selector syntax.
        """
        query_json = json.dumps(query)
        code = build_bim_tool_code(
            f"""
query = {query_json}
try:
    rows = None
    try:
        from ifcquery import select as ifc_select  # pylint: disable=import-error
        rows = ifc_select.select(model, query)
    except Exception:
        from ifcopenshell.util.selector import filter_elements  # pylint: disable=import-error
        entities = list(filter_elements(model, query))
        rows = [
            {{
                "id": int(entity.id()),
                "type": entity.is_a(),
                "guid": getattr(entity, "GlobalId", None),
                "name": getattr(entity, "Name", None),
            }}
            for entity in entities
        ]
    result = {{"status": "ok", "query": query, "count": len(rows), "items": rows}}
except Exception as ex:
    result = {{"status": "error", "error": f"Selector query failed: {{type(ex).__name__}}: {{ex}}", "query": query}}
"""
        )
        return send_code(code, strict_json=True)
