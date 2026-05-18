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
            title="BIM Load IFC",
            destructiveHint=True,
        )
    )
    def bim_load_ifc(path: str) -> dict[str, object]:
        """
        Load an IFC file into Bonsai's active IFC session.
        """
        path_json = json.dumps(path)
        code = build_bim_tool_code(
            f"""
import os
path = {path_json}
if not path or not os.path.isfile(path):
    result = {{"status": "error", "error": f"IFC path not found: '{{path}}'"}}
else:
    try:
        IfcStore.load_file(path)
        model = IfcStore.get_file()
        try:
            import bonsai.tool as tool  # pylint: disable=import-error
            tool.Ifc.after_file_loaded()
            tool.Ifc.rebuild_element_maps()
        except Exception:
            pass
        result = {{
            "status": "ok",
            "path": IfcStore.path or path,
            "schema": model.schema if model else "",
            "entity_count": sum(1 for _ in model) if model else 0,
        }}
    except Exception as ex:
        result = {{"status": "error", "error": f"Failed to load IFC '{{path}}': {{type(ex).__name__}}: {{ex}}"}}
""",
            require_ifc=False,
            with_tool=True,
        )
        return send_code(code, strict_json=True)
