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


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Clash Check",
            readOnlyHint=True,
        )
    )
    def bim_clash(
        element_id: int,
        clearance: float = 0.0,
        tolerance: float = 0.002,
        scope: str = "storey",
    ) -> dict[str, object]:
        """
        Run geometric clash / clearance checks for an IFC element.
        """
        code = build_bim_tool_code(
            f"""
element_id = {int(element_id)}
clearance = {float(clearance)}
tolerance = {float(tolerance)}
scope = {scope!r}
ent = model.by_id(element_id)
if ent is None:
    result = {{"status": "error", "error": f"Element #{{element_id}} not found."}}
else:
    try:
        from ifcquery import clash as clash_mod  # pylint: disable=import-error
    except Exception as ex:
        result = {{
            "status": "error",
            "error": f"ifcquery not available for clash detection: {{type(ex).__name__}}: {{ex}}",
        }}
    else:
        try:
            payload = clash_mod.clash(
                model,
                ent,
                clearance=clearance if clearance > 0.0 else None,
                tolerance=tolerance,
                scope=scope,
            )
            result = {{"status": "ok", "element_id": element_id, "clash": payload}}
        except Exception as ex:
            result = {{"status": "error", "error": f"Clash check failed: {{type(ex).__name__}}: {{ex}}"}}
"""
        )
        return send_code(code, strict_json=True)
