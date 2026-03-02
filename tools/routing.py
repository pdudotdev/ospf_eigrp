"""Routing table and policy tools: get_routing, get_routing_policies."""
from urllib.parse import quote
from core.inventory import devices
from platforms.platform_map import PLATFORM_MAP
from transport import execute_command
from input_models.models import RoutingQuery, RoutingPolicyQuery
from tools import _error_response


async def get_routing(params: RoutingQuery) -> dict:
    """
    Retrieve routing table information from a device.

    - If prefix is provided → targeted route lookup.
    - If prefix is omitted → full routing table.

    Use this tool to verify route presence, next-hop selection,
    and routing protocol contributions.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    try:
        base_cmd = PLATFORM_MAP[device["cli_style"]]["routing_table"]["ip_route"]
    except KeyError:
        return _error_response(params.device, f"Routing not supported on {device['cli_style'].upper()}")

    if not params.prefix:
        action = base_cmd
    elif isinstance(base_cmd, dict):
        # RouterOS REST: append prefix as a query parameter on the path
        action = dict(base_cmd)
        action["path"] = f"{base_cmd['path']}?dst-address={quote(params.prefix, safe='')}"
    else:
        # IOS / EOS: append prefix to the CLI command string
        action = f"{base_cmd} {params.prefix}"

    return await execute_command(params.device, action)


async def get_routing_policies(params: RoutingPolicyQuery) -> dict:
    """
    Retrieve routing policy configuration from a device.

    Use this tool to inspect route maps, prefix lists, access lists,
    and policy-based routing that may influence routing decisions.

    Supported queries:
    - redistribution         → View routing protocol redistribution
    - route_maps             → View route-map definitions
    - prefix_lists           → Inspect prefix filtering rules
    - policy_based_routing   → Verify PBR configuration
    - access_lists           → Review ACLs affecting routing or filtering
    - nat_pat               → Check NAT/PAT translations and rules

    Notes:
    - Supported queries vary by platform.
    - Results may be cached briefly.
    - Use nat_pat only on NAT_EDGE devices (R2C, R3C, R18M, R19M) after ruling out routing issues.

    Recommended usage:
    - Use when routes are filtered, modified, or unexpectedly redirected.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    try:
        action = PLATFORM_MAP[device["cli_style"]]["routing_policies"][params.query]
    except KeyError:
        return _error_response(params.device, f"Routing policy query '{params.query}' not supported on {device['cli_style'].upper()}")

    return await execute_command(params.device, action)
