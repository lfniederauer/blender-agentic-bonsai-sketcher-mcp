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
            title="BIM Quantify",
            readOnlyHint=True,
        )
    )
    def bim_quantify(
        ifc_class: str = "",
        element_ids: list[int] | None = None,
    ) -> dict[str, object]:
        """
        Aggregate quantity takeoff values from Qto_* property sets.
        """
        ifc_class_json = json.dumps(ifc_class)
        element_ids_json = json.dumps(element_ids)
        code = build_bim_tool_code(
            f"""
ifc_class = {ifc_class_json}
element_ids = {element_ids_json}
try:
    from ifcopenshell.util.element import get_psets  # pylint: disable=import-error
except Exception as ex:
    result = {{"status": "error", "error": f"ifcopenshell.util.element unavailable: {{type(ex).__name__}}: {{ex}}"}}
else:
    elements = []
    if element_ids:
        for eid in element_ids:
            ent = model.by_id(int(eid))
            if ent is not None:
                elements.append(ent)
    elif ifc_class:
        elements = list(model.by_type(ifc_class))
    else:
        elements = list(model.by_type("IfcProduct"))
    totals = {{}}
    processed = 0
    max_elements = 5000
    for ent in elements:
        processed += 1
        if processed > max_elements:
            break
        psets = get_psets(ent, include_inherited=True, include_type=True)
        for pset_name, props in psets.items():
            if not pset_name.startswith("Qto_"):
                continue
            for prop_name, value in props.items():
                if isinstance(value, (int, float)):
                    key = f"{{pset_name}}.{{prop_name}}"
                    totals[key] = totals.get(key, 0.0) + float(value)
    result = {{
        "status": "ok",
        "ifc_class": ifc_class or None,
        "element_ids_count": len(element_ids) if element_ids else None,
        "processed": min(processed, max_elements),
        "truncated": processed > max_elements,
        "totals": [
            {{"quantity": name, "value": value}}
            for name, value in sorted(totals.items())
        ],
    }}
"""
        )
        return send_code(code, strict_json=True)
