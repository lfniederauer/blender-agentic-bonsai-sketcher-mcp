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

_CODE = build_bim_tool_code(
    """
try:
    hierarchy = None
    try:
        from ifcquery import tree as ifc_tree  # pylint: disable=import-error
        hierarchy = ifc_tree.tree(model)
    except Exception:
        def node_payload(ent):
            return {
                "id": int(ent.id()),
                "type": ent.is_a(),
                "name": getattr(ent, "Name", None),
                "guid": getattr(ent, "GlobalId", None),
                "children": [],
            }

        roots = model.by_type("IfcProject")
        built = []
        for root in roots:
            root_payload = node_payload(root)
            queue = [(root, root_payload)]
            while queue:
                parent_ent, parent_payload = queue.pop(0)
                children = []
                for rel in getattr(parent_ent, "IsDecomposedBy", []) or []:
                    for child in getattr(rel, "RelatedObjects", []) or []:
                        children.append(child)
                for rel in getattr(parent_ent, "ContainsElements", []) or []:
                    for child in getattr(rel, "RelatedElements", []) or []:
                        children.append(child)
                for child in children:
                    child_payload = node_payload(child)
                    parent_payload["children"].append(child_payload)
                    queue.append((child, child_payload))
            built.append(root_payload)
        hierarchy = built
    result = {"status": "ok", "tree": hierarchy}
except Exception as ex:
    result = {"status": "error", "error": f"Failed to compute spatial tree: {type(ex).__name__}: {ex}"}
"""
)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="BIM Spatial Tree",
            readOnlyHint=True,
        )
    )
    def bim_tree() -> dict[str, object]:
        """
        Return IFC spatial hierarchy (Project -> Site -> Building -> Storeys).
        """
        return send_code(_CODE, strict_json=True)
