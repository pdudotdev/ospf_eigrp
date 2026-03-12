"""Configuration push tool: push_config, validate_commands, and forbidden command sets."""
import asyncio
import json
import logging
import time

from core.inventory import devices

log = logging.getLogger("ainoc.tools.config")
from transport.ssh import push_ssh
from tools.state import assess_risk
from tools import _error_response
from input_models.models import ConfigCommand, RiskInput

# Forbidden CLI command substrings — matched case-insensitively against any CLI command.
# NOTE: Matching is substring-based. IOS abbreviations (e.g. "rel" for "reload",
# "wr er" for "write erase") are a known limitation — this list covers the most
# dangerous full-form commands. A full IOS parser would be required to close this gap.
FORBIDDEN = {
    # Device-level destructive operations
    "reload", "write erase", "erase", "format", "delete", "boot",
    "crypto key",        # covers: zeroize, generate, export
    # Configuration persistence — prevents saving bad state as startup config
    "copy run",          # copy running-config startup-config, copy run start
    "write mem",         # write memory
    # Wholesale config replacement — unpredictable and irreversible
    "configure replace",
    # Credential and AAA manipulation
    "username ",         # trailing space reduces false positives in descriptions
    "enable secret",
    "enable password",
    "snmp-server community",
    # Routing process removal (high blast-radius)
    "no router",
    # Interface reset — clears all sub-config
    "default interface",
    # Management plane lockout
    "transport input none",
    # State-clearing commands that cause temporary outages
    "clear ip ospf", "clear ip bgp", "clear ip route",
    # Diagnostic overload — can saturate CPU on production devices
    "debug all",
}


def _generate_rollback_advisory(commands: list[str]) -> list[str]:
    """Generate advisory rollback commands (not automatically applied)."""
    rollback = []
    for cmd in commands:
        stripped = cmd.strip()
        if stripped.lower().startswith("no "):
            rollback.append(stripped[3:].strip())
        else:
            rollback.append(f"no {stripped}")
    return rollback


def validate_commands(cmds: list[str]) -> None:
    """Raise ValueError if any command matches a forbidden pattern."""
    for c in cmds:
        c_lower = c.lower()  # no strip — FORBIDDEN patterns include trailing spaces for precision
        if any(bad in c_lower for bad in FORBIDDEN):
            log.error("forbidden command blocked: %r", c)
            raise ValueError(f"Forbidden command detected: {c}")


async def _push_to_device(dev_name: str, device: dict, commands: list[str]) -> tuple[str, dict]:
    """Dispatch config push to the correct transport.

    All transports use SSH CLI push — simple and reliable for IOS-XE commands.
    - asyncssh: Scrapli SSH (A1C, A2C, IAN, IBN).
    - restconf: Scrapli SSH fallback (C1C, C2C, E1C, E2C, X1C).
    """
    return await push_ssh(device, dev_name, commands)


async def _push_to_device_safe(dev_name: str, device: dict, commands: list[str]) -> tuple[str, object]:
    try:
        return await _push_to_device(dev_name, device, commands)
    except Exception as e:
        return dev_name, _error_response(dev_name, f"ERROR: {e}")


async def push_config(params: ConfigCommand) -> dict:
    """
    Push configuration commands to one or more devices.

    IMPORTANT:
    - Risk assessment is advisory only and does not block changes.
    """
    log.info("push_config START: devices=%s commands=%s", params.devices, params.commands)

    # Guard: all devices must share the same cli_style — commands are vendor-specific
    known_devices     = {d: devices[d]["cli_style"] for d in params.devices if d in devices}
    cli_styles_present = set(known_devices.values())
    if len(cli_styles_present) > 1:
        return {
            "error":      "Mixed cli_style in device list. Push to each vendor group separately.",
            "cli_styles": known_devices,
        }

    risk = await assess_risk(RiskInput(devices=params.devices, commands=params.commands))

    start = time.perf_counter()
    try:
        validate_commands(params.commands)
    except ValueError as e:
        return {"error": str(e)}

    tasks   = []
    results = {}
    for dev_name in params.devices:
        device = devices.get(dev_name)
        if not device:
            results[dev_name] = _error_response(dev_name, "Unknown device")
            continue
        tasks.append(
            asyncio.create_task(
                _push_to_device_safe(dev_name, device, params.commands)
            )
        )

    for dev_name, result in await asyncio.gather(*tasks):
        results[dev_name] = result

    end = time.perf_counter()
    log.info("push_config RESULT: %s", json.dumps({k: v for k, v in results.items()}, default=str))
    results["execution_time_seconds"] = round(end - start, 2)
    results["risk_assessment"]        = risk
    results["rollback_advisory"]      = _generate_rollback_advisory(params.commands)
    return results
