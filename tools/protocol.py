"""Protocol diagnostic tools: get_ospf, get_eigrp, get_bgp."""
from core.inventory import devices
from platforms.platform_map import PLATFORM_MAP
from transport import execute_command
from input_models.models import OspfQuery, EigrpQuery, BgpQuery
from tools import _error_response


async def get_ospf(params: OspfQuery) -> dict:
    """
    Retrieve OSPF operational data from a network device.

    Use this tool to investigate OSPF adjacency, database, and configuration
    issues during troubleshooting.

    Supported queries:
    - neighbors   → Check OSPF neighbor state and adjacency health
    - database    → Inspect LSDB contents and LSA propagation
    - borders     → Identify ABRs/ASBRs and inter-area routing
    - config      → Review OSPF configuration on the device
    - interfaces  → Verify OSPF-enabled interfaces and parameters
    - details     → Vendor-specific detailed OSPF information (if available)

    Notes:
    - Not all queries are supported on all platforms.
    - If a query is unsupported, the tool returns an error.
    - Results may be served from cache (short-lived) to improve efficiency.
    - Use this tool before running generic show commands.

    Recommended usage:
    - Start with "neighbors" to verify adjacency.
    - Use "database" when investigating missing routes.
    - Use "config" to confirm intent vs actual configuration.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    try:
        action = PLATFORM_MAP[device["cli_style"]]["ospf"][params.query]
    except KeyError:
        return _error_response(params.device, f"OSPF query '{params.query}' not supported on platform {device['cli_style'].upper()}")

    return await execute_command(params.device, action)


async def get_eigrp(params: EigrpQuery) -> dict:
    """
    Retrieve EIGRP operational data from an IOS device.

    Use this tool to troubleshoot EIGRP neighbor relationships, topology
    information, interface participation, and configuration issues.

    Supported queries:
    - neighbors   → Verify EIGRP adjacencies and peer health
    - topology    → Inspect feasible successors and route calculations
    - interfaces  → Confirm interfaces participating in EIGRP
    - config      → Review EIGRP configuration

    Notes:
    - EIGRP is supported only on IOS devices.
    - If a query is unsupported, the tool returns an error.
    - Cached results may be returned for short periods.

    Recommended usage:
    - Start with "neighbors" to verify adjacency.
    - Use "topology" when routes are missing or not preferred.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    if device["cli_style"] != "ios":
        return _error_response(params.device, "EIGRP is supported only on IOS devices")

    try:
        action = PLATFORM_MAP["ios"]["eigrp"][params.query]
    except KeyError:
        return _error_response(params.device, f"Unsupported EIGRP query: {params.query}")

    return await execute_command(params.device, action)


async def get_bgp(params: BgpQuery) -> dict:
    """
    Retrieve BGP operational data from a network device.

    Use this tool to investigate BGP session state, route exchange,
    and configuration during routing issues.

    Supported queries:
    - summary  → Check neighbor state, uptime, and prefixes exchanged
    - table    → Inspect detailed BGP table and path attributes
    - config   → Review BGP configuration

    Notes:
    - Supported queries vary by platform.
    - Cached results may be returned briefly for efficiency.

    Recommended usage:
    - Start with "summary" to verify session health.
    - Use "table" when routes are missing or path selection is unexpected.

    Use this tool before falling back to run_show.
    """
    device = devices.get(params.device)
    if not device:
        return _error_response(params.device, f"Unknown device: {params.device}")

    try:
        action = PLATFORM_MAP[device["cli_style"]]["bgp"][params.query]
    except KeyError:
        return _error_response(params.device, f"BGP query '{params.query}' not supported on platform {device['cli_style'].upper()}")

    return await execute_command(params.device, action)
