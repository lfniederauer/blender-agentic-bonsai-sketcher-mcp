# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from agents.agent import create_bim_costs_agent
from agents.tools import generate_content_config_for_mixed_builtin_and_function_tools


def test_mixed_tool_generate_content_config_sets_server_side_invocations():
    config = generate_content_config_for_mixed_builtin_and_function_tools()
    assert config.tool_config is not None
    assert config.tool_config.include_server_side_tool_invocations is True


def test_bim_costs_agent_sets_mixed_tool_config_when_research_tools_present(monkeypatch):
    monkeypatch.setattr(
        "agents.agent.build_optional_research_tools",
        lambda: ["google_search_stub"],
    )
    agent = create_bim_costs_agent()
    assert agent.generate_content_config is not None
    assert agent.generate_content_config.tool_config.include_server_side_tool_invocations is True
