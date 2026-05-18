#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Run unit tests inside the Docker test image (or locally with BLENDER_MCP_HTTP_URL).

Requires the blender-mcp HTTP service when BLENDER_MCP_HTTP_URL is set.
"""

from __future__ import annotations

import os
import subprocess
import sys

_REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_UNIT_SCRIPTS = (
    "tests/test_rst_parse.py",
    "tests/test_rst_search.py",
    "tests/test_mcp_server.py",
    "tests/test_tool_listing.py",
    "tests/test_mcp_http.py",
)

_PYTEST_TARGETS = (
    "tests/test_knowledge_loader.py",
)


def _run(cmd: list[str]) -> None:
    print("\n==> {:s}".format(" ".join(cmd)), flush=True)
    subprocess.run(cmd, cwd=_REPO_DIR, check=True)


def main() -> int:
    if not os.environ.get("BLENDER_MCP_HTTP_URL"):
        print(
            "ERROR: BLENDER_MCP_HTTP_URL must be set (Docker test stack or export manually).",
            file=sys.stderr,
        )
        return 1

    for script in _UNIT_SCRIPTS:
        _run([sys.executable, script])

    _run([sys.executable, "-m", "pytest", *_PYTEST_TARGETS, "-q"])
    print("\nAll unit tests passed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
