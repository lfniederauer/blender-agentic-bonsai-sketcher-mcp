# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
HTTP transport smoke tests for the blender-mcp Docker service.

Skipped unless ``BLENDER_MCP_HTTP_URL`` is set. Run via ``make test`` (Docker)
or export the URL after ``make test_up``.
"""

__all__ = ()

import json
import os
import unittest
import urllib.error
import urllib.request

from tests.utils.mcp_connect import call_server_tool, mcp_http_url, query_server

_BIM_TOOL_NAMES = {
    "bim_add_pset",
    "bim_assign_spatial",
    "bim_clash",
    "bim_create_element",
    "bim_edit",
    "bim_execute_bonsai_op",
    "bim_highlight_elements",
    "bim_ifc_to_object",
    "bim_info",
    "bim_load_ifc",
    "bim_object_to_ifc",
    "bim_quantify",
    "bim_save_ifc",
    "bim_select",
    "bim_status",
    "bim_summary",
    "bim_sync_selection",
    "bim_tree",
    "bim_validate",
}


def _health_url() -> str:
    base = mcp_http_url()
    assert base is not None
    return base.rstrip("/") + "/health"


@unittest.skipUnless(mcp_http_url(), "BLENDER_MCP_HTTP_URL is not set")
class TestMCPHttpService(unittest.TestCase):
    """
    Verify the streamable HTTP MCP deployment (Docker blender-mcp).
    """

    def test_health_endpoint(self) -> None:
        with urllib.request.urlopen(_health_url(), timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(payload.get("status"), "healthy")
        self.assertEqual(payload.get("service"), "blender-mcp")

    def test_list_tools_includes_bim(self) -> None:
        data = query_server()
        names = {tool["name"] for tool in data["tools"]}
        missing = sorted(_BIM_TOOL_NAMES - names)
        self.assertFalse(missing, "Missing BIM tools over HTTP: {!r}".format(missing))
        self.assertIn("execute_blender_code", names)

    def test_search_api_docs_over_http(self) -> None:
        payload = call_server_tool(
            "search_api_docs",
            {"query": "module:: bpy.data", "max_results": 3},
        )
        hits = payload.get("hits", [])
        paths = [hit["path"] for hit in hits]
        self.assertIn("api/bpy.data.rst", paths)
