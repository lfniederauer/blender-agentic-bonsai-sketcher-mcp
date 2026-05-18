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
            title="BIM Save IFC",
            destructiveHint=True,
        )
    )
    def bim_save_ifc(path: str = "") -> dict[str, object]:
        """
        Save the current Bonsai IFC model to disk.
        """
        path_json = json.dumps(path)
        code = build_bim_tool_code(
            f"""
import os
path = {path_json}
target = path or IfcStore.path
if not target:
    result = {{"status": "error", "error": "No output path provided and active IFC has no source path."}}
else:
    try:
        directory = os.path.dirname(target)
        if directory:
            os.makedirs(directory, exist_ok=True)
        model.write(target)
        IfcStore.path = target
        result = {{"status": "ok", "path": target, "entity_count": sum(1 for _ in model)}}
    except Exception as ex:
        result = {{"status": "error", "error": f"Failed to save IFC to '{{target}}': {{type(ex).__name__}}: {{ex}}"}}
"""
        )
        return send_code(code, strict_json=True)
