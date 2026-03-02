"""Arista EOS eAPI executor (HTTPS JSON-RPC)."""
from core.settings import VERIFY_TLS
from transport.pool import get_eapi_session


async def execute_eapi(device: dict, command: str):
    """Execute a show command via eAPI JSON-RPC. Returns the result list or an error dict."""
    url = f"https://{device['host']}/command-api"
    payload = {
        "jsonrpc": "2.0",
        "method":  "runCmds",
        "params":  {"version": 1, "cmds": [command]},
        "id":      1,
    }
    session = await get_eapi_session()
    async with session.post(url, json=payload, ssl=VERIFY_TLS) as resp:
        if resp.status != 200:
            return {"error": f"eAPI returned HTTP {resp.status}", "device": device["host"]}
        data = await resp.json()
        # JSON-RPC errors arrive as HTTP 200 with an "error" key instead of "result"
        if "error" in data:
            return {"device": device["host"], "error": data["error"]}
        return data["result"]


async def push_eapi(device: dict, dev_name: str, commands: list[str]) -> tuple[str, dict]:
    """Push configuration commands via eAPI JSON-RPC."""
    url = f"https://{device['host']}/command-api"
    payload = {
        "jsonrpc": "2.0",
        "method":  "runCmds",
        "params":  {
            "version": 1,
            # Prepend "enable" and "configure" to enter privileged config mode before commands
            "cmds":    ["enable", "configure"] + commands,
            "format":  "text",
        },
        "id": 1,
    }
    session = await get_eapi_session()
    async with session.post(url, json=payload, ssl=VERIFY_TLS) as resp:
        if resp.status != 200:
            return dev_name, {"transport_used": "eapi", "error": f"eAPI returned HTTP {resp.status}"}
        data = await resp.json()
        # JSON-RPC errors arrive as HTTP 200 with an "error" key instead of "result"
        if "error" in data:
            return dev_name, {"transport_used": "eapi", "error": data["error"]}
        return dev_name, {"transport_used": "eapi", "result": data.get("result", data)}
