"""UT-028 — MCP Server tool registration: verify all 15 tools are registered.

Tests for MCPServer.py — validates that every expected tool is registered on
the FastMCP instance and that no tool is accidentally omitted after refactoring.

Validates:
- All 15 expected tool names are registered
- No extra tools are present (strict equality)
- Tool count is exactly 15

Design note: MCPServer.py calls setup_logging() at import time, which sets
propagate=False on the 'ainoc' logger. To avoid breaking pytest caplog in later
test files, setup_logging() is patched to a no-op during import.
"""
import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_TOOLS = {
    "get_ospf",
    "get_bgp",
    "get_routing",
    "get_routing_policies",
    "get_interfaces",
    "ping",
    "traceroute",
    "run_show",
    "get_intent",
    "assess_risk",
    "push_config",
    "jira_add_comment",
    "jira_resolve_issue",
    "request_approval",
    "post_approval_outcome",
}


def _get_mcp():
    """Import MCPServer and return the FastMCP instance.

    Patches setup_logging() to a no-op so it does not permanently set
    propagate=False on the 'ainoc' logger — that would break caplog in later tests.
    """
    if "MCPServer" in sys.modules:
        return sys.modules["MCPServer"].mcp
    with patch("core.logging_config.setup_logging"):
        import MCPServer
    return MCPServer.mcp


def test_all_15_tools_registered():
    """All 15 expected MCP tool names must be registered — no additions, no omissions."""
    mcp = _get_mcp()
    tools = asyncio.run(mcp.list_tools())
    registered = {t.name for t in tools}
    missing = EXPECTED_TOOLS - registered
    extra = registered - EXPECTED_TOOLS
    assert not missing, f"Tools missing from MCP registration: {missing}"
    assert not extra, f"Unexpected tools registered (update EXPECTED_TOOLS if intentional): {extra}"


def test_tool_count_is_15():
    """Exactly 15 tools must be registered — catches both additions and removals."""
    mcp = _get_mcp()
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 15, (
        f"Expected 15 registered tools, got {len(tools)}. "
        f"Registered: {sorted(t.name for t in tools)}"
    )
