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
            title="BIM Validate",
            readOnlyHint=True,
        )
    )
    def bim_validate(express_rules: bool = False) -> dict[str, object]:
        """
        Validate IFC model in Bonsai (optionally including EXPRESS rules).
        """
        code = build_bim_tool_code(
            f"""
express_rules = {bool(express_rules)}
try:
    payload = None
    try:
        from ifcquery import validate as validate_mod  # pylint: disable=import-error
        payload = validate_mod.validate(model, express_rules=express_rules)
    except Exception:
        issues = []
        invalid = 0
        checked = 0
        max_checked = 5000
        for ent in model:
            checked += 1
            if checked > max_checked:
                break
            try:
                ent.get_info(include_identifier=True)
            except Exception as ex:
                invalid += 1
                if len(issues) < 100:
                    issues.append({{"id": int(ent.id()), "type": ent.is_a(), "error": f"{{type(ex).__name__}}: {{ex}}"}})
        payload = {{
            "valid": invalid == 0,
            "issues": issues,
            "issue_count": invalid,
            "checked_count": checked,
            "fallback": True,
        }}
    result = {{"status": "ok", "express_rules": express_rules, "validation": payload}}
except Exception as ex:
    result = {{"status": "error", "error": f"Validation failed: {{type(ex).__name__}}: {{ex}}"}}
"""
        )
        return send_code(code, strict_json=True)
