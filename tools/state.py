"""Network state tools: get_intent, assess_risk."""
import json
import logging
import os

log = logging.getLogger("ainoc.tools.state")

from core.inventory import devices
from input_models.models import EmptyInput, RiskInput

_BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_INTENT_FILE = os.path.join(_BASE_DIR, "intent",  "INTENT.json")
_PATHS_FILE  = os.path.join(_BASE_DIR, "sla_paths", "paths.json")

# Roles that make a device a critical control-plane node
_HIGH_RISK_ROLES = {"ABR", "ASBR", "IGP_REDISTRIBUTOR", "NAT_EDGE", "ROUTE_REFLECTOR"}


async def get_intent(params: EmptyInput) -> dict:
    """Return the desired network intent."""
    if not os.path.exists(_INTENT_FILE):
        raise RuntimeError("INTENT.json not found")
    with open(_INTENT_FILE) as f:
        return json.load(f)




async def assess_risk(params: RiskInput) -> dict:
    """
    Assigns a simple risk level (low / medium / high) to a configuration change.
    This tool does NOT block changes. It only reports risk.
    """
    cmd_text     = " ".join(params.commands).lower()
    device_count = len(params.devices)
    risk         = "low"
    reasons      = []

    # ── Device count ─────────────────────────────────────────────────────────
    if device_count >= 3:
        risk = "high"
        reasons.append(f"Change affects {device_count} devices")
    elif device_count > 1:
        risk = "medium"
        reasons.append(f"Change affects multiple devices ({device_count})")

    # ── Critical device roles from INTENT.json ────────────────────────────────
    try:
        with open(_INTENT_FILE) as f:
            intent = json.load(f)
        routers = intent.get("routers", {})
        for dev_name in params.devices:
            dev_roles = set(routers.get(dev_name, {}).get("roles", []))
            critical = dev_roles & _HIGH_RISK_ROLES
            if critical:
                risk = "high"
                reasons.append(f"{dev_name} has critical role(s): {', '.join(sorted(critical))}")
    except Exception as e:
        log.warning("assess_risk: could not load INTENT.json: %s", e)

    # ── SLA path impact from paths.json ───────────────────────────────────────
    try:
        with open(_PATHS_FILE) as f:
            sla_paths = json.load(f).get("paths", [])
        affected = {p["id"] for p in sla_paths
                    if any(d in p.get("scope_devices", []) for d in params.devices)}
        if len(affected) >= 3:
            risk = "high"
            reasons.append(f"Change affects {len(affected)} SLA monitoring paths")
        elif affected:
            if risk == "low":
                risk = "medium"
            reasons.append(f"Change affects {len(affected)} SLA monitoring path(s)")
    except Exception as e:
        log.warning("assess_risk: could not load paths.json: %s", e)

    # ── Command content ───────────────────────────────────────────────────────
    if any(k in cmd_text for k in ("router ", "ospf", "bgp", "isis")):
        risk = "high"
        reasons.append("Touches routing control plane")

    if "shutdown" in cmd_text and "no shutdown" not in cmd_text:
        risk = "high"
        reasons.append("Interface disruption possible")

    return {
        "risk":    risk,
        "devices": device_count,
        "reasons": reasons or ["Minor configuration change"],
    }
