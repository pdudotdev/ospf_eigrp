"""
IT-003 — Full MCP Tool Coverage

Ports testing/tool_tests.py to pytest. Verifies connectivity and tool correctness
for all three platform types (IOS, EOS, RouterOS) and validates cache behavior.
Includes push_config CRUD tests (loopback create/verify/delete) per vendor.

Requires live device access.
"""

import asyncio
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Skip all tests in this module if NO_LAB is set (e.g. in CI without a running lab)
pytestmark = pytest.mark.skipif(
    os.environ.get("NO_LAB", "0") == "1",
    reason="Lab not running — set NO_LAB=0 to enable integration tests",
)

from transport          import execute_command
from tools.protocol     import get_ospf, get_eigrp, get_bgp
from tools.routing      import get_routing, get_routing_policies
from tools.operational  import get_interfaces, ping, traceroute, run_show
from tools.config       import push_config
from input_models.models import (
    OspfQuery,
    EigrpQuery,
    BgpQuery,
    InterfacesQuery,
    RoutingQuery,
    RoutingPolicyQuery,
    PingInput,
    TracerouteInput,
    ShowCommand,
    ConfigCommand,
)


# ── device constants (mirror tool_tests.py) ───────────────────────────────────

IOS1 = "R3C"
IOS2 = "R5C"
IOS3 = "R8C"

EOS1 = "R1A"
EOS2 = "R6A"
EOS3 = "R7A"

ROS1 = "R18M"
ROS2 = "R19M"
ROS3 = "R20M"


# ── results collection ───────────────────────────────────────────────────────

RESULTS: list[dict] = []
RESULTS_FILE = Path(__file__).parent / "test_mcp_tools_results.md"


def _format_output(output) -> str:
    """Format test output for Markdown display."""
    if isinstance(output, (dict, list)):
        try:
            return json.dumps(output, indent=2, default=str)
        except (TypeError, ValueError):
            return str(output)
    return str(output)


def record(section: str, test_name: str, device: str, transport: str, output):
    """Append a single test result to the collection."""
    RESULTS.append({
        "section": section,
        "test": test_name,
        "device": device,
        "transport": transport,
        "output": output,
    })


def record_crud(section: str, test_name: str, device: str, phases: dict):
    """Append a multi-phase (CRUD) test result to the collection."""
    RESULTS.append({
        "section": section,
        "test": test_name,
        "device": device,
        "phases": phases,
    })


@pytest.fixture(autouse=True, scope="session")
def write_results_file():
    """Yield to let all tests run, then write collected results to Markdown."""
    yield

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# IT-003 — MCP Tool Test Results",
        f"*Generated: {timestamp} UTC*",
        "",
    ]

    sections: OrderedDict[str, list] = OrderedDict()
    for entry in RESULTS:
        sections.setdefault(entry["section"], []).append(entry)

    for sec_title, entries in sections.items():
        lines.append(f"## {sec_title}")
        lines.append("")
        for entry in entries:
            if "phases" in entry:
                lines.append(f"### {entry['test']} ({entry['device']})")
                lines.append("")
                for phase_name, phase_output in entry["phases"].items():
                    lines.append(f"#### {phase_name}")
                    lines.append("```json")
                    lines.append(_format_output(phase_output))
                    lines.append("```")
                    lines.append("")
            else:
                lines.append(f"### {entry['test']} ({entry['device']} — {entry['transport']})")
                lines.append("```json")
                lines.append(_format_output(entry["output"]))
                lines.append("```")
                lines.append("")

    RESULTS_FILE.write_text("\n".join(lines), encoding="utf-8")


# ── helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.run(coro)


# ── IT-003a: platform connectivity ────────────────────────────────────────────

def test_connectivity_ios():
    """IT-003a-1: SSH to Cisco IOS (R3C) — show version."""
    result = run(execute_command(IOS1, "show version"))
    record("IT-003a: Platform Connectivity", "test_connectivity_ios", IOS1, "SSH", result)
    assert result, "Expected non-empty result from execute_command(R3C)"
    text = str(result)
    assert "version" in text.lower(), f"Expected version info, got: {text[:200]}"


def test_connectivity_eos():
    """IT-003a-2: eAPI to Arista EOS (R1A) — show version."""
    result = run(execute_command(EOS1, "show version"))
    record("IT-003a: Platform Connectivity", "test_connectivity_eos", EOS1, "eAPI", result)
    assert result, "Expected non-empty result from execute_command(R1A)"
    text = str(result)
    assert "version" in text.lower(), f"Expected version info, got: {text[:200]}"


def test_connectivity_ros():
    """IT-003a-3: REST to MikroTik RouterOS (R18M) — GET /rest/ip/route."""
    action = {"method": "GET", "path": "/rest/ip/route"}
    result = run(execute_command(ROS1, action))
    record("IT-003a: Platform Connectivity", "test_connectivity_ros", ROS1, "REST", result)
    assert result, "Expected non-empty result from execute_command(R18M)"


# ── IT-003b: protocol tools ────────────────────────────────────────────────────

def test_ospf_eos():
    """IT-003b-1: get_ospf neighbors on EOS (R1A)."""
    result = run(get_ospf(OspfQuery(device=EOS1, query="neighbors")))
    record("IT-003b: Protocol Tools", "test_ospf_eos", EOS1, "eAPI", result)
    assert result, "Expected non-empty OSPF result from R1A"
    text = str(result)
    assert "error" not in text.lower() or "neighbor" in text.lower(), (
        f"Unexpected error in OSPF result: {text[:200]}"
    )


def test_eigrp_ios():
    """IT-003b-2: get_eigrp neighbors on IOS (R3C)."""
    result = run(get_eigrp(EigrpQuery(device=IOS1, query="neighbors")))
    record("IT-003b: Protocol Tools", "test_eigrp_ios", IOS1, "SSH", result)
    assert result, "Expected non-empty EIGRP result from R3C"
    text = str(result)
    assert "error" not in text.lower() or "neighbor" in text.lower(), (
        f"Unexpected error in EIGRP result: {text[:200]}"
    )


def test_bgp_ros():
    """IT-003b-3: get_bgp summary on RouterOS (R18M)."""
    result = run(get_bgp(BgpQuery(device=ROS1, query="summary")))
    record("IT-003b: Protocol Tools", "test_bgp_ros", ROS1, "REST", result)
    assert result, "Expected non-empty BGP result from R18M"


def test_bgp_neighbors_ios():
    """IT-003b-3b: get_bgp neighbors on IOS (R2C) with neighbor IP filter."""
    result = run(get_bgp(BgpQuery(device="R2C", query="neighbors", neighbor="200.40.40.2")))
    record("IT-003b: Protocol Tools", "test_bgp_neighbors_ios", "R2C", "SSH", result)
    assert result, "Expected non-empty BGP neighbors result from R2C"
    assert "error" not in result, f"get_bgp neighbors failed: {result}"


def test_interfaces_ros():
    """IT-003b-4: get_interfaces on RouterOS (R19M)."""
    result = run(get_interfaces(InterfacesQuery(device=ROS2, query="interface_status")))
    record("IT-003b: Protocol Tools", "test_interfaces_ros", ROS2, "REST", result)
    assert result, "Expected non-empty interfaces result from R19M"


def test_routing_ios():
    """IT-003b-5: get_routing prefix lookup on IOS (R5C)."""
    result = run(get_routing(RoutingQuery(device=IOS2, prefix="10.0.0.9")))
    record("IT-003b: Protocol Tools", "test_routing_ios", IOS2, "SSH", result)
    assert result, "Expected non-empty routing result from R5C"


def test_ping_eos():
    """IT-003b-6: ping from EOS (R6A) to 10.1.1.5."""
    result = run(ping(PingInput(device=EOS2, destination="10.1.1.5")))
    record("IT-003b: Protocol Tools", "test_ping_eos", EOS2, "eAPI", result)
    assert result, "Expected non-empty ping result from R6A"
    text = str(result)
    assert "success" in text.lower() or "!" in text or "bytes" in text.lower(), (
        f"Ping appears to have failed: {text[:200]}"
    )


def test_routing_policies_ios():
    """IT-003b-7: get_routing_policies route_maps on IOS (R8C)."""
    result = run(get_routing_policies(RoutingPolicyQuery(device=IOS3, query="route_maps")))
    record("IT-003b: Protocol Tools", "test_routing_policies_ios", IOS3, "SSH", result)
    assert result, "Expected non-empty routing policies result from R8C"


def test_traceroute_ros():
    """IT-003b-8: traceroute from RouterOS (R20M)."""
    result = run(traceroute(TracerouteInput(device=ROS3, destination="172.16.77.2")))
    record("IT-003b: Protocol Tools", "test_traceroute_ros", ROS3, "REST", result)
    assert result, "Expected non-empty traceroute result from R20M"


def test_run_show_eos():
    """IT-003b-9: run_show fallback on EOS (R7A)."""
    result = run(run_show(ShowCommand(device=EOS3, command="show ip arp")))
    record("IT-003b: Protocol Tools", "test_run_show_eos", EOS3, "eAPI", result)
    assert result, "Expected non-empty run_show result from R7A"


def test_run_show_routeros():
    """IT-003b-9b: run_show fallback on RouterOS (R18M) — GET to /rest/interface."""
    cmd = json.dumps({"method": "GET", "path": "/rest/interface"})
    result = run(run_show(ShowCommand(device=ROS1, command=cmd)))
    record("IT-003b: Protocol Tools", "test_run_show_routeros", ROS1, "REST", result)
    assert result, "Expected non-empty run_show result from R18M"
    assert "error" not in result, f"run_show RouterOS GET failed: {result}"


def test_redistribution_ros():
    """IT-003b-10: get_routing_policies redistribution on RouterOS (R18M)."""
    result = run(get_routing_policies(RoutingPolicyQuery(device=ROS1, query="redistribution")))
    record("IT-003b: Protocol Tools", "test_redistribution_ros", ROS1, "REST", result)
    assert result, "Expected non-empty redistribution result from R18M"


# ── IT-003c: cache behavior ────────────────────────────────────────────────────

def test_cache_behavior():
    """IT-003c: execute_command caching — miss, hit, miss after TTL (6s sleep)."""
    import time

    device = IOS1
    command = "show clock"

    r1 = run(execute_command(device, command))
    assert r1.get("cache_hit") is False, f"First call should be a cache miss, got: {r1.get('cache_hit')}"

    r2 = run(execute_command(device, command))
    assert r2.get("cache_hit") is True, f"Second call (within TTL) should be a cache hit, got: {r2.get('cache_hit')}"

    time.sleep(6)  # CMD_TTL = 5s

    r3 = run(execute_command(device, command))
    assert r3.get("cache_hit") is False, f"Third call (after TTL) should be a cache miss, got: {r3.get('cache_hit')}"

    record("IT-003c: Cache Behavior", "test_cache_behavior", IOS1, "SSH",
           {"call_1_miss": r1, "call_2_hit": r2, "call_3_miss_after_ttl": r3})


# ── IT-003d: push_config (Loopback CRUD) ─────────────────────────────────────

def test_push_config_ios():
    """IT-003d-1: push_config loopback CRUD on IOS (R3C — SSH)."""
    device = IOS1
    phases = {}

    # Create Loopback99
    create_cmds = [
        "interface Loopback99",
        "ip address 10.99.99.1 255.255.255.255",
        "no shutdown",
    ]
    create_result = run(push_config(ConfigCommand(devices=[device], commands=create_cmds)))
    phases["Create"] = create_result
    assert device in create_result, f"Expected {device} key in push_config result"

    try:
        # Verify Loopback99 exists
        verify_result = run(get_interfaces(InterfacesQuery(device=device)))
        phases["Verify"] = verify_result
        text = str(verify_result)
        assert "Loopback99" in text, f"Loopback99 not found after creation: {text[:300]}"
    finally:
        # Delete Loopback99 (always runs for cleanup)
        delete_cmds = ["no interface Loopback99"]
        delete_result = run(push_config(ConfigCommand(devices=[device], commands=delete_cmds)))
        phases["Delete"] = delete_result

    record_crud("IT-003d: push_config (Loopback CRUD)", "test_push_config_ios", device, phases)


def test_push_config_eos():
    """IT-003d-2: push_config loopback CRUD on EOS (R1A — eAPI)."""
    device = EOS1
    phases = {}

    # Create Loopback99
    create_cmds = [
        "interface Loopback99",
        "ip address 10.99.99.1/32",
    ]
    create_result = run(push_config(ConfigCommand(devices=[device], commands=create_cmds)))
    phases["Create"] = create_result
    assert device in create_result, f"Expected {device} key in push_config result"

    try:
        # Verify Loopback99 exists
        verify_result = run(get_interfaces(InterfacesQuery(device=device)))
        phases["Verify"] = verify_result
        text = str(verify_result)
        assert "Loopback99" in text, f"Loopback99 not found after creation: {text[:300]}"
    finally:
        # Delete Loopback99 (always runs for cleanup)
        delete_cmds = ["no interface Loopback99"]
        delete_result = run(push_config(ConfigCommand(devices=[device], commands=delete_cmds)))
        phases["Delete"] = delete_result

    record_crud("IT-003d: push_config (Loopback CRUD)", "test_push_config_eos", device, phases)


def test_push_config_ros():
    """IT-003d-3: push_config loopback CRUD on RouterOS (R18M — REST)."""
    device = ROS1
    phases = {}
    bridge_id = None

    # Create bridge "Loopback99" via PUT
    create_cmd = json.dumps({
        "method": "PUT",
        "path": "/rest/interface/bridge",
        "body": {"name": "Loopback99", "comment": "Test loopback"},
    })
    create_result = run(push_config(ConfigCommand(devices=[device], commands=[create_cmd])))
    phases["Create"] = create_result
    assert device in create_result, f"Expected {device} key in push_config result"

    # Extract .id from REST response for cleanup
    try:
        rest_response = create_result[device]["result"][0]
        bridge_id = rest_response.get(".id")
    except (KeyError, IndexError, TypeError, AttributeError):
        bridge_id = None

    try:
        # Verify Loopback99 exists
        verify_result = run(get_interfaces(InterfacesQuery(device=device)))
        phases["Verify"] = verify_result
        text = str(verify_result)
        assert "Loopback99" in text, f"Loopback99 not found after creation: {text[:300]}"
    finally:
        # Delete bridge Loopback99 (always runs for cleanup)
        if not bridge_id:
            # Fallback: GET all bridges and find Loopback99 by name
            try:
                bridges_action = {"method": "GET", "path": "/rest/interface/bridge"}
                bridges_result = run(execute_command(device, bridges_action))
                bridge_list = bridges_result.get("parsed") or bridges_result.get("raw", [])
                if isinstance(bridge_list, list):
                    for bridge in bridge_list:
                        if isinstance(bridge, dict) and bridge.get("name") == "Loopback99":
                            bridge_id = bridge.get(".id")
                            break
            except Exception:
                pass

        if bridge_id:
            delete_cmd = json.dumps({
                "method": "DELETE",
                "path": f"/rest/interface/bridge/{bridge_id}",
            })
        else:
            # Last resort: attempt name-based path
            delete_cmd = json.dumps({
                "method": "DELETE",
                "path": "/rest/interface/bridge/Loopback99",
            })

        delete_result = run(push_config(ConfigCommand(devices=[device], commands=[delete_cmd])))
        phases["Delete"] = delete_result

    record_crud("IT-003d: push_config (Loopback CRUD)", "test_push_config_ros", device, phases)
