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
            title="BIM Element Info",
            readOnlyHint=True,
        )
    )
    def bim_info(element_id: int) -> dict[str, object]:
        """
        Return deep element info for an IFC STEP id.
        """
        code = build_bim_tool_code(
            f"""
element_id = {int(element_id)}
element = model.by_id(element_id)
if element is None:
    result = {{"status": "error", "error": f"Element #{{element_id}} not found."}}
else:
    try:
        payload = None
        try:
            from ifcquery import info as ifc_info  # pylint: disable=import-error
            payload = ifc_info.info(model, element)
        except Exception:
            payload = element.get_info(recursive=True, include_identifier=True)
        result = {{"status": "ok", "element_id": element_id, "info": payload}}
    except Exception as ex:
        result = {{"status": "error", "error": f"Failed to inspect #{{element_id}}: {{type(ex).__name__}}: {{ex}}"}}
"""
        )
        return send_code(code, strict_json=True)
