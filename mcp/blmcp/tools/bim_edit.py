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
            title="BIM Edit API",
            destructiveHint=True,
        )
    )
    def bim_edit(function_path: str, params: str = "{}") -> dict[str, object]:
        """
        Execute an ifcopenshell.api mutation on the Bonsai-loaded IFC model.
        """
        function_path_json = json.dumps(function_path)
        params_json = json.dumps(params)
        code = build_bim_tool_code(
            f"""
function_path = {function_path_json}
params_raw = {params_json}
if "." not in function_path:
    result = {{"status": "error", "error": "function_path must be in 'module.function' format."}}
else:
    module, function = function_path.split(".", 1)
    try:
        import json
        import ifcopenshell.api  # pylint: disable=import-error
        kwargs = json.loads(params_raw) if isinstance(params_raw, str) and params_raw.strip() else {{}}
        if not isinstance(kwargs, dict):
            raise TypeError("params must decode to a JSON object")
        out = ifcopenshell.api.run(f"{{module}}.{{function}}", model, **kwargs)
        try:
            json.dumps(out)
            payload = out
        except Exception:
            payload = repr(out)
        result = {{
            "status": "ok",
            "function_path": function_path,
            "params": kwargs,
            "result": payload,
        }}
        try:
            import bonsai.tool as tool  # pylint: disable=import-error
            tool.Ifc.rebuild_element_maps()
        except Exception:
            pass
    except Exception as ex:
        result = {{
            "status": "error",
            "function_path": function_path,
            "error": f"ifcopenshell.api.run failed: {{type(ex).__name__}}: {{ex}}",
        }}
""",
            with_ifcopenshell=True,
            with_tool=False,
        )
        return send_code(code, strict_json=True)
