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
            title="BIM Create Element",
            destructiveHint=True,
        )
    )
    def bim_create_element(ifc_class: str, params: str = "{}") -> dict[str, object]:
        """
        Create a new IFC element via Bonsai/IfcOpenShell APIs.
        """
        ifc_class_json = json.dumps(ifc_class)
        params_json = json.dumps(params)
        code = build_bim_tool_code(
            f"""
ifc_class = {ifc_class_json}
params_raw = {params_json}
if not ifc_class or not ifc_class.startswith("Ifc"):
    result = {{"status": "error", "error": "ifc_class must start with 'Ifc'."}}
else:
    try:
        import json
        kwargs = json.loads(params_raw) if isinstance(params_raw, str) and params_raw.strip() else {{}}
        if not isinstance(kwargs, dict):
            raise TypeError("params must decode to a JSON object")
        if "ifc_class" in kwargs:
            kwargs.pop("ifc_class")
        entity = tool.Ifc.run("root.create_entity", ifc_class=ifc_class, **kwargs)
        try:
            tool.Ifc.rebuild_element_maps()
        except Exception:
            pass
        result = {{
            "status": "ok",
            "ifc_class": ifc_class,
            "element": {{
                "id": int(entity.id()),
                "type": entity.is_a(),
                "guid": getattr(entity, "GlobalId", None),
                "name": getattr(entity, "Name", None),
            }},
        }}
    except Exception as ex:
        result = {{"status": "error", "error": f"Create element failed: {{type(ex).__name__}}: {{ex}}"}}
""",
            with_tool=True,
        )
        return send_code(code, strict_json=True)
