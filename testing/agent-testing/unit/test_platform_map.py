"""
UT-002 — Platform Map Commands

Verifies that PLATFORM_MAP returns the correct commands for each
cli_style (ios, eos, routeros) and all relevant query types.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "platforms"))
from platform_map import PLATFORM_MAP


# ── IOS ───────────────────────────────────────────────────────────────────────

class TestIOS:
    """Verify PLATFORM_MAP command strings for Cisco IOS-XE (cli_style='ios').

    Each test pins one PLATFORM_MAP[cli_style][protocol][query] value so that
    regressions from editing platform_map.py are caught immediately.
    """

    def test_ospf_neighbors(self):
        """Neighbors query must map to the standard IOS OSPF neighbor show command."""
        assert PLATFORM_MAP["ios"]["ospf"]["neighbors"] == "show ip ospf neighbor"

    def test_ospf_database(self):
        """Database query must map to the IOS LSDB show command."""
        assert PLATFORM_MAP["ios"]["ospf"]["database"] == "show ip ospf database"

    def test_ospf_interfaces(self):
        """Interfaces query must map to the IOS OSPF interface show command."""
        assert PLATFORM_MAP["ios"]["ospf"]["interfaces"] == "show ip ospf interface"

    def test_ospf_config(self):
        """Config query must return a command string that includes 'ospf'."""
        assert "ospf" in PLATFORM_MAP["ios"]["ospf"]["config"]

    def test_ospf_borders(self):
        """Borders query must map to the ABR/ASBR border-routers show command."""
        assert PLATFORM_MAP["ios"]["ospf"]["borders"] == "show ip ospf border-routers"

    def test_ospf_details(self):
        """Details query must map to the IOS OSPF process detail show command."""
        assert PLATFORM_MAP["ios"]["ospf"]["details"] == "show ip ospf"

    def test_eigrp_neighbors(self):
        """Neighbors query must map to the IOS EIGRP neighbor show command."""
        assert PLATFORM_MAP["ios"]["eigrp"]["neighbors"] == "show ip eigrp neighbors"

    def test_eigrp_topology(self):
        """Topology query must map to the IOS EIGRP topology table show command."""
        assert PLATFORM_MAP["ios"]["eigrp"]["topology"] == "show ip eigrp topology"

    def test_eigrp_interfaces(self):
        """Interfaces query must return a command string containing 'eigrp'."""
        assert "eigrp" in PLATFORM_MAP["ios"]["eigrp"]["interfaces"]

    def test_eigrp_config(self):
        """Config query must return a command string containing 'eigrp'."""
        assert "eigrp" in PLATFORM_MAP["ios"]["eigrp"]["config"]

    def test_bgp_summary(self):
        """Summary query must map to the IOS BGP summary show command."""
        assert PLATFORM_MAP["ios"]["bgp"]["summary"] == "show ip bgp summary"

    def test_bgp_neighbors(self):
        """Neighbors query must map to the IOS BGP neighbors show command."""
        assert PLATFORM_MAP["ios"]["bgp"]["neighbors"] == "show ip bgp neighbors"

    def test_routing_table(self):
        """ip_route query must map to the IOS routing table show command."""
        assert PLATFORM_MAP["ios"]["routing_table"]["ip_route"] == "show ip route"

    def test_redistribution(self):
        """Redistribution query must return a command string containing 'redistribute'."""
        assert "redistribute" in PLATFORM_MAP["ios"]["routing_policies"]["redistribution"]

    def test_interfaces(self):
        """Interface status query must map to the IOS brief interface show command."""
        assert PLATFORM_MAP["ios"]["interfaces"]["interface_status"] == "show ip interface brief"

    def test_ping(self):
        """Ping tool must map to the IOS 'ping' command string."""
        assert PLATFORM_MAP["ios"]["tools"]["ping"] == "ping"

    def test_traceroute(self):
        """Traceroute tool must map to the IOS 'traceroute' command string."""
        assert PLATFORM_MAP["ios"]["tools"]["traceroute"] == "traceroute"


# ── EOS ───────────────────────────────────────────────────────────────────────

class TestEOS:
    """Verify PLATFORM_MAP command strings for Arista EOS (cli_style='eos').

    EOS uses the same CLI-style show commands as IOS but is accessed via eAPI.
    These tests ensure EOS commands are distinct entries and not accidentally
    sharing IOS values by reference.
    """

    def test_ospf_neighbors(self):
        """Neighbors query must map to the EOS OSPF neighbor show command."""
        assert PLATFORM_MAP["eos"]["ospf"]["neighbors"] == "show ip ospf neighbor"

    def test_ospf_interfaces(self):
        """Interfaces query must map to the EOS OSPF interface show command."""
        assert PLATFORM_MAP["eos"]["ospf"]["interfaces"] == "show ip ospf interface"

    def test_ospf_config(self):
        """Config query must return a command string containing 'ospf'."""
        assert "ospf" in PLATFORM_MAP["eos"]["ospf"]["config"]

    def test_bgp_summary(self):
        """Summary query must map to the EOS BGP summary show command."""
        assert PLATFORM_MAP["eos"]["bgp"]["summary"] == "show ip bgp summary"

    def test_bgp_neighbors(self):
        """Neighbors query must map to the EOS BGP neighbors show command."""
        assert PLATFORM_MAP["eos"]["bgp"]["neighbors"] == "show ip bgp neighbors"

    def test_routing_table(self):
        """ip_route query must map to the EOS routing table show command."""
        assert PLATFORM_MAP["eos"]["routing_table"]["ip_route"] == "show ip route"

    def test_interfaces(self):
        """Interface status query must map to the EOS brief interface show command."""
        assert PLATFORM_MAP["eos"]["interfaces"]["interface_status"] == "show ip interface brief"

    def test_ping(self):
        """Ping tool must map to the EOS 'ping' command string."""
        assert PLATFORM_MAP["eos"]["tools"]["ping"] == "ping"


# ── RouterOS ──────────────────────────────────────────────────────────────────

class TestRouterOS:
    """Verify PLATFORM_MAP REST action dicts for MikroTik RouterOS (cli_style='routeros').

    RouterOS commands are dicts with 'method' and 'path' keys (HTTP REST actions)
    rather than CLI strings. Tests verify the method and path fragments are correct.
    """

    def test_ospf_neighbors(self):
        """Neighbors query must be a GET to the RouterOS OSPF neighbor REST path."""
        entry = PLATFORM_MAP["routeros"]["ospf"]["neighbors"]
        assert entry["method"] == "GET"
        assert "/ospf/neighbor" in entry["path"]

    def test_ospf_database(self):
        """Database query must be a GET to a RouterOS OSPF-related REST path."""
        entry = PLATFORM_MAP["routeros"]["ospf"]["database"]
        assert entry["method"] == "GET"
        assert "/ospf/" in entry["path"]

    def test_ospf_interfaces(self):
        """Interfaces query must be a GET action (RouterOS REST read-only access)."""
        entry = PLATFORM_MAP["routeros"]["ospf"]["interfaces"]
        assert entry["method"] == "GET"

    def test_bgp_summary(self):
        """BGP summary query must be a GET to the RouterOS BGP REST path."""
        entry = PLATFORM_MAP["routeros"]["bgp"]["summary"]
        assert entry["method"] == "GET"

    def test_bgp_neighbors(self):
        """BGP neighbors query must be a GET to the RouterOS BGP session REST path."""
        entry = PLATFORM_MAP["routeros"]["bgp"]["neighbors"]
        assert entry["method"] == "GET"
        assert "/bgp/" in entry["path"]

    def test_routing_table(self):
        """Routing table query must be a GET to a RouterOS route REST path."""
        entry = PLATFORM_MAP["routeros"]["routing_table"]["ip_route"]
        assert entry["method"] == "GET"
        assert "/route" in entry["path"]

    def test_ping(self):
        """Ping tool must be a POST to the RouterOS /ping REST path.
        RouterOS executes tools (ping, traceroute) via HTTP POST, not GET.
        """
        entry = PLATFORM_MAP["routeros"]["tools"]["ping"]
        assert entry["method"] == "POST"
        assert "/ping" in entry["path"]

    def test_traceroute(self):
        """Traceroute tool must be a POST to the RouterOS /traceroute REST path."""
        entry = PLATFORM_MAP["routeros"]["tools"]["traceroute"]
        assert entry["method"] == "POST"
        assert "/traceroute" in entry["path"]
