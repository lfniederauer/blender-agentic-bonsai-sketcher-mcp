# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Load agent knowledge markdown from agents/knowledge/ for ADK and Cursor.

Topic keys (use with load_topic / load_topics / knowledge_for_role):

  index          — README.md (index + status legend)
  mcp            — MCP tools, execute_blender_code, CAD Sketcher inspection
  slab-sketcher  — Named sketch → IfcSlab (bim.add_slab_from_sketch, cad_sketch_profile_name,
                   import_cad_sketcher, deploy/correction context — implement only on user command)
"""
from __future__ import annotations

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

TOPIC_FILES: dict[str, str] = {
    "mcp": "mcp-blender-investigation.md",
    "slab-sketcher": "bonsai-slab-from-cad-sketcher.md",
}

_ROLE_TOPICS: dict[str, tuple[str, ...]] = {
    "coordinator": ("index",),
    "geometry": ("mcp", "slab-sketcher"),
    "appearance": ("mcp",),
    "properties": ("mcp", "slab-sketcher"),
    "costs": (),
    "inspector": ("mcp",),
    "researcher": (),
}


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_topic(topic: str) -> str:
    """Return one knowledge document by topic key."""
    if topic == "index":
        return _read_markdown(KNOWLEDGE_DIR / "README.md")
    filename = TOPIC_FILES.get(topic)
    if not filename:
        raise KeyError(f"Unknown knowledge topic: {topic!r}")
    path = KNOWLEDGE_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Knowledge file not found: {path}")
    return _read_markdown(path)


def load_topics(*topics: str) -> str:
    """Concatenate multiple topics for injection into agent instructions."""
    if not topics:
        return ""
    parts = [load_topic(topic) for topic in topics]
    return "\n\n---\n\n".join(parts)


def load_all_except_readme() -> str:
    """Load every topic file (not README)."""
    return load_topics(*TOPIC_FILES.keys())


def knowledge_for_role(role: str) -> str:
    """Knowledge block sized for an ADK agent role."""
    topics = _ROLE_TOPICS.get(role)
    if topics is None:
        raise KeyError(f"Unknown role: {role!r}")
    if not topics:
        return ""
    body = load_topics(*topics)
    return f"\n\n## Workspace knowledge ({role})\n\nFollow this runbook before MCP calls:\n\n{body}\n"


def knowledge_index_blurb() -> str:
    """Short pointer for the coordinator (full docs delegated to specialists)."""
    index = load_topic("index")
    return f"""
## Agent knowledge base

Specialists must apply runbooks in `agents/knowledge/` before Blender MCP work.
Read the index below; delegate geometry/slab/sketch tasks to bim_geometry and IFC tasks to bim_properties.

{index}
"""
