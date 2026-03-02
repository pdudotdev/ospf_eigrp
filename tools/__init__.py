# tools package


def _error_response(device: str | None, message: str) -> dict:
    """Return a consistently-shaped error dict for all tool functions.

    All tool errors use {"error": "...", "device": "..."} shape.
    device is omitted when not meaningful (e.g. inventory lookup failures
    where the device name itself is the unknown value).
    """
    resp = {"error": message}
    if device:
        resp["device"] = device
    return resp
