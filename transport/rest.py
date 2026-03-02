"""MikroTik RouterOS REST API executor (HTTP/HTTPS)."""
import json
from core.settings import VERIFY_TLS, ROUTEROS_HTTPS
from transport.pool import get_rest_session


async def execute_rest(device: dict, action: dict):
    """Execute a REST query against RouterOS. Returns the response body or an error dict."""
    scheme = "https" if ROUTEROS_HTTPS else "http"
    url    = f"{scheme}://{device['host']}{action['path']}"
    method = action.get("method", "GET").upper()
    session = await get_rest_session()

    if method == "GET":
        async with session.get(url, ssl=VERIFY_TLS) as resp:
            if resp.status != 200:
                return {"error": f"RouterOS REST returned HTTP {resp.status}", "path": action["path"]}
            return await resp.json()

    elif method in ("POST", "PUT", "PATCH"):
        payload = action.get("body") or action.get("default_body", {})
        # getattr dispatch avoids a separate branch per HTTP method; method is validated upstream
        async with getattr(session, method.lower())(url, json=payload, ssl=VERIFY_TLS) as resp:
            # RouterOS returns 200 for updates, 201 for newly created resources
            if resp.status not in (200, 201):
                return {"error": f"RouterOS REST returned HTTP {resp.status}", "path": action["path"]}
            return await resp.json()

    elif method == "DELETE":
        async with session.delete(url, ssl=VERIFY_TLS) as resp:
            # RouterOS returns 200 with body or 204 No Content on successful DELETE
            if resp.status not in (200, 204):
                return {"error": f"RouterOS REST returned HTTP {resp.status}", "path": action["path"]}
            text = await resp.text()
            return json.loads(text) if text.strip() else {"status": "deleted"}

    else:
        return {"error": f"Unsupported HTTP method: {method}"}


async def push_rest(device: dict, dev_name: str, commands: list[str]) -> tuple[str, dict]:
    """Execute a list of JSON-encoded RouterOS REST actions for config push."""
    results = []
    for cmd in commands:
        try:
            action = json.loads(cmd)
        except json.JSONDecodeError:
            results.append(f"ERROR: Invalid JSON action for RouterOS: {cmd}")
            continue
        result = await execute_rest(device, action)
        results.append(result)
    return dev_name, {"transport_used": "rest", "result": results}
