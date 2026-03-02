"""Operational tools: get_interfaces, ping, traceroute, run_show."""
from core.inventory import devices
from platforms.platform_map import PLATFORM_MAP
from transport import execute_command
from input_models.models import InterfacesQuery, PingInput, TracerouteInput, ShowCommand
from tools import _error_response


async def get_interfaces(params: InterfacesQuery) -> dict:
    """
    Retrieve interface status and IP information from a device.

    Use this tool to verify interface state, IP assignments, and operational
    status during connectivity and routing investigations.

    Notes:
    - Command syntax is vendor-specific and resolved via COMMAND_MAP.
    - Returns a summary view of interfaces.
    - Results may be cached briefly.

    Recommended usage:
    - Use when troubleshooting down links or missing adjacencies.
    - Use to confirm IP addressing and interface operational state.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    try:
        action = PLATFORM_MAP[device["cli_style"]]["interfaces"]["interface_status"]
    except KeyError:
        return _error_response(params.device, f"Interface status not supported on {device['cli_style'].upper()}")

    return await execute_command(params.device, action)


async def ping(params: PingInput) -> dict:
    """
    Test reachability from a device to a destination IP.

    Use this tool to verify connectivity, validate routing decisions,
    and detect packet loss or reachability failures.

    Notes:
    - Command syntax is vendor-specific and resolved via COMMAND_MAP.
    - Source parameter is optional and may not be supported on all platforms.
    - Results are cached briefly.

    Recommended usage:
    - Use after verifying routing to confirm data-plane reachability.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    cli_style = device["cli_style"]
    base = PLATFORM_MAP[cli_style]["tools"]["ping"]

    if isinstance(base, dict):
        action = base.copy()
        action["body"] = {"address": params.destination}
    else:
        action = f"{base} {params.destination}"

    if params.source and cli_style in ("ios", "eos"):
        action += f" source {params.source}"

    return await execute_command(params.device, action)


async def traceroute(params: TracerouteInput) -> dict:
    """
    Trace the path from a device to a destination IP.

    Use this tool to identify routing paths, loops, asymmetric routing,
    or where traffic is being dropped.

    Notes:
    - Command syntax is vendor-specific and resolved via COMMAND_MAP.
    - Output format varies by platform.
    - Results are cached briefly.
    - Source parameter is optional and may not be supported on all platforms.

    Recommended usage:
    - Use when ping succeeds but path is unexpected.
    - Use to locate where packets are dropped.
    - Provide source=<ip> (from sla_paths source_ip field) to force traceroute on the monitored path.
    - Use only when necessary.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    cli_style = device["cli_style"]
    base = PLATFORM_MAP[cli_style]["tools"]["traceroute"]

    if isinstance(base, dict):
        action = base.copy()
        action["body"] = {"address": params.destination, **base.get("default_body", {})}
        if params.source and cli_style == "routeros":
            action["body"]["src-address"] = params.source
    else:
        action = f"{base} {params.destination}"
        if params.source and cli_style in ("ios", "eos"):
            action += f" source {params.source}"

    return await execute_command(params.device, action)


async def run_show(params: ShowCommand) -> dict:
    """Run a show command against a network device."""
    return await execute_command(params.device, params.command, ttl=0)
