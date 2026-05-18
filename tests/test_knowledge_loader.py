# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for agents/knowledge_loader.py."""
from __future__ import annotations

import pytest

from agents.knowledge_loader import (
    KNOWLEDGE_DIR,
    load_topic,
    load_topics,
    knowledge_for_role,
)


def test_knowledge_dir_exists() -> None:
    assert KNOWLEDGE_DIR.is_dir()


def test_load_topic_index() -> None:
    text = load_topic("index")
    assert "Agent knowledge base" in text


def test_load_topic_mcp() -> None:
    text = load_topic("mcp")
    assert "entities.all" in text
    assert "get_object_detail_summary" in text


def test_load_topic_slab_sketcher() -> None:
    text = load_topic("slab-sketcher")
    assert "planta" in text
    assert "edit_sketch_extrusion_profile" in text
    assert "add_slab_from_sketch" in text
    assert "cad_sketch_profile_name" in text
    assert "Correction context" in text


def test_load_topics_joins() -> None:
    text = load_topics("mcp", "slab-sketcher")
    assert "---" in text
    assert "planta" in text
    assert "entities.all" in text


def test_knowledge_for_role_geometry() -> None:
    text = knowledge_for_role("geometry")
    assert "Workspace knowledge (geometry)" in text
    assert "planta" in text


def test_knowledge_for_role_coordinator() -> None:
    text = knowledge_for_role("coordinator")
    assert "index" in text.lower() or "Agent knowledge base" in text


def test_knowledge_for_role_costs_empty() -> None:
    assert knowledge_for_role("costs") == ""


def test_unknown_topic_raises() -> None:
    with pytest.raises(KeyError):
        load_topic("nonexistent")
