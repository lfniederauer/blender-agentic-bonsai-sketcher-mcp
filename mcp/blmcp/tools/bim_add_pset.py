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
            title="BIM Add Property Set",
            destructiveHint=True,
        )
    )
    def bim_add_pset(element_id: int, name: str, properties: str = "{}") -> dict[str, object]:
        """
        Add or update a property set on an IFC element.
        """
        element_id_int = int(element_id)
        name_json = json.dumps(name)
        properties_json = json.dumps(properties)
        code = build_bim_tool_code(
            f"""
element_id = {element_id_int}
pset_name = {name_json}
properties_raw = {properties_json}
element = model.by_id(element_id)
if element is None:
    result = {{"status": "error", "error": f"Element #{{element_id}} not found."}}
else:
    try:
        import json
        props = json.loads(properties_raw) if isinstance(properties_raw, str) and properties_raw.strip() else {{}}
        if not isinstance(props, dict):
            raise TypeError("properties must decode to a JSON object")
        pset = tool.Ifc.run("pset.add_pset", product=element, name=pset_name)
        if props:
            tool.Ifc.run("pset.edit_pset", pset=pset, properties=props)
        try:
            tool.Ifc.rebuild_element_maps()
        except Exception:
            pass
        result = {{
            "status": "ok",
            "element_id": element_id,
            "pset_id": int(pset.id()),
            "pset_name": pset_name,
            "properties": props,
        }}
    except Exception as ex:
        result = {{"status": "error", "error": f"Pset update failed: {{type(ex).__name__}}: {{ex}}"}}
""",
            with_tool=True,
        )
        return send_code(code, strict_json=True)
