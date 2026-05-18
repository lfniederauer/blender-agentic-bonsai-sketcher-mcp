# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

from blmcp.tools_helpers.bonsai_helpers import build_bim_status_code
from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_CODE = build_bim_status_code(
    """
result = {
    "status": "ok",
    "bonsai_installed": False,
    "ifcopenshell_installed": False,
    "ifc_loaded": False,
    "ifc_path": "",
    "schema": "",
    "entity_count": 0,
    "active_object": None,
}
active = bpy.context.view_layer.objects.active
result["active_object"] = active.name if active else None
try:
    import ifcopenshell  # pylint: disable=import-error,unused-import
    result["ifcopenshell_installed"] = True
except Exception:
    pass
try:
    from bonsai.bim.ifc import IfcStore  # pylint: disable=import-error
    result["bonsai_installed"] = True
    model = IfcStore.get_file()
    if model is not None:
        result["ifc_loaded"] = True
        result["ifc_path"] = IfcStore.path or ""
        result["schema"] = model.schema
        result["entity_count"] = sum(1 for _ in model)
except Exception as ex:
    result["bonsai_error"] = f"{type(ex).__name__}: {ex}"
"""
)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Status",
            readOnlyHint=True,
        )
    )
    def bim_status() -> dict[str, object]:
        """
        Return Bonsai / IFC readiness status for the current Blender session.
        """
        return send_code(_CODE, strict_json=True)
