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
            title="BIM Execute Bonsai Operator",
            destructiveHint=True,
        )
    )
    def bim_execute_bonsai_op(operator: str, params: str = "{}") -> dict[str, object]:
        """
        Execute a Bonsai bpy.ops operator (e.g. "bim.add_wall").
        """
        operator_json = json.dumps(operator)
        params_json = json.dumps(params)
        code = build_bim_tool_code(
            f"""
operator = {operator_json}
params_raw = {params_json}
if "." not in operator:
    result = {{"status": "error", "error": "operator must be in '<module>.<op>' format."}}
else:
    module_name, op_name = operator.split(".", 1)
    ops_module = getattr(bpy.ops, module_name, None)
    if ops_module is None or not hasattr(ops_module, op_name):
        result = {{"status": "error", "error": f"Operator '{{operator}}' not found."}}
    else:
        try:
            import json
            kwargs = json.loads(params_raw) if isinstance(params_raw, str) and params_raw.strip() else {{}}
            if not isinstance(kwargs, dict):
                raise TypeError("params must decode to a JSON object")
            if getattr(bpy.context, "mode", "OBJECT") != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode="OBJECT")
                except Exception:
                    pass
            op_fn = getattr(ops_module, op_name)
            op_result = op_fn(**kwargs)
            result = {{"status": "ok", "operator": operator, "result": op_result}}
        except Exception as ex:
            result = {{"status": "error", "error": f"Operator '{{operator}}' failed: {{type(ex).__name__}}: {{ex}}"}}
""",
            require_ifc=False,
            with_bpy=True,
            with_tool=False,
        )
        return send_code(code, strict_json=True)
