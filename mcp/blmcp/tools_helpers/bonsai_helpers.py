# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Helpers to generate Bonsai/IfcOpenShell tool code for Blender execution.

These helpers build Python code strings that run inside Blender via the MCP bridge.
They standardize imports, error handling, and IFC session checks to reduce duplication.
"""

from __future__ import annotations

__all__ = (
    "build_bim_tool_code",
    "build_bim_status_code",
    "build_ifc_run_code",
    "build_rebuild_maps_code",
    "indent_code",
)


def indent_code(code: str, spaces: int = 4) -> str:
    """Indent a multi-line snippet by the given number of spaces."""
    prefix = " " * spaces
    stripped = code.strip("\n")
    if not stripped:
        return ""
    return "\n".join(f"{prefix}{line}" if line else line for line in stripped.splitlines())


def build_bim_tool_code(
    body: str,
    *,
    require_ifc: bool = True,
    with_bpy: bool = False,
    with_ifcopenshell: bool = False,
    with_ifcquery: bool = False,
    with_tool: bool = True,
    prelude: str = "",
) -> str:
    """
    Wrap Blender-side BIM tool code with standardized imports and checks.

    Parameters:
    - body: The tool logic to execute after dependencies are verified.
    - require_ifc: Require a loaded IFC model in Bonsai before executing body.
    - with_bpy/with_ifcopenshell/with_ifcquery/with_tool: Add imports.
    - prelude: Optional code inserted before the IFC load check.
    """
    imports: list[str] = []
    if with_bpy:
        imports.append("import bpy  # pylint: disable=import-error")
    if with_tool:
        imports.append("import bonsai.tool as tool  # pylint: disable=import-error")
    imports.append("from bonsai.bim.ifc import IfcStore  # pylint: disable=import-error")
    if with_ifcopenshell:
        imports.append("import ifcopenshell  # pylint: disable=import-error")
    if with_ifcquery:
        imports.append("import ifcquery  # pylint: disable=import-error")

    imports_block = "\n    ".join(imports)
    prelude_block = indent_code(prelude, 4)
    body_block = indent_code(body, 4)

    ifc_guard = ""
    if require_ifc:
        ifc_guard = "\n    model = IfcStore.get_file()\n    if model is None:\n        result = {\"status\": \"error\", \"error\": \"No IFC loaded in Bonsai.\"}\n    else:\n"
        if prelude_block:
            prelude_block = indent_code(prelude, 8)
        if body_block:
            body_block = indent_code(body, 8)

    return f"""
result = {{"status": "ok"}}
try:
    {imports_block}
except Exception as ex:
    result = {{"status": "error", "error": f"BIM dependencies unavailable: {{type(ex).__name__}}: {{ex}}"}}
else:{ifc_guard}
{prelude_block}
{body_block}
"""


def build_bim_status_code(body: str) -> str:
    """
    Build a status tool body with optional Bonsai/IfcOpenShell checks.

    Unlike build_bim_tool_code, this does not error on missing Bonsai,
    allowing the tool to report availability.
    """
    body_block = indent_code(body, 4)
    return f"""
result = {{"status": "ok"}}
try:
    import bpy  # pylint: disable=import-error
except Exception as ex:
    result = {{"status": "error", "error": f"Blender context unavailable: {{type(ex).__name__}}: {{ex}}"}}
else:
{body_block}
"""


def build_ifc_run_code(function_path: str, params_json: str) -> str:
    """
    Build a tool.Ifc.run call for Bonsai inside Blender.

    Params are provided as a JSON string to allow deferred parsing in Blender.
    """
    return f"""
function_path = {function_path!s}
params_raw = {params_json}
try:
    import json
    import bonsai.tool as tool  # pylint: disable=import-error
except Exception as ex:
    result = {{"status": "error", "error": f"Bonsai unavailable: {{type(ex).__name__}}: {{ex}}"}}
else:
    try:
        kwargs = json.loads(params_raw) if isinstance(params_raw, str) and params_raw.strip() else {{}}
        if not isinstance(kwargs, dict):
            raise TypeError("params must decode to a JSON object")
        out = tool.Ifc.run(function_path, **kwargs)
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
    except Exception as ex:
        result = {{
            "status": "error",
            "function_path": function_path,
            "error": f"tool.Ifc.run failed: {{type(ex).__name__}}: {{ex}}",
        }}
"""


def build_rebuild_maps_code() -> str:
    """Return a snippet to rebuild Bonsai element maps if available."""
    return """
try:
    import bonsai.tool as tool  # pylint: disable=import-error
    tool.Ifc.rebuild_element_maps()
except Exception:
    pass
"""
