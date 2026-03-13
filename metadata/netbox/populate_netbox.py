#!/usr/bin/env python3
"""Populate NetBox with aiNOC device inventory.

Creates all prerequisite objects (custom fields, manufacturer, device types,
platform, roles, sites) and 9 devices with management interfaces and IPs.

Idempotent — safe to run multiple times. Existing objects are reused, not duplicated.

Usage:
    python metadata/netbox/populate_netbox.py

Reads NETBOX_URL and NETBOX_TOKEN from .env or environment variables.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    import pynetbox
except ImportError:
    print("ERROR: pynetbox not installed. Run: pip install pynetbox")
    sys.exit(1)


# ── Connection ────────────────────────────────────────────────────────────────

NETBOX_URL = os.getenv("NETBOX_URL", "").strip()
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "").strip()

if not NETBOX_URL or not NETBOX_TOKEN:
    print("ERROR: NETBOX_URL and NETBOX_TOKEN must be set in .env")
    sys.exit(1)

nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

# Verify connectivity
try:
    nb.status()
except Exception as exc:
    print(f"ERROR: Cannot connect to NetBox at {NETBOX_URL}: {exc}")
    sys.exit(1)

print(f"Connected to NetBox at {NETBOX_URL}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_or_create(endpoint, slug=None, name=None, model=None, **kwargs):
    """Get an existing object by slug (preferred) or name, or create it.

    Use 'model' instead of 'name' for device types (NetBox v4.5 requirement).
    """
    obj = None
    if slug is not None:
        obj = endpoint.get(slug=slug)
    elif name is not None:
        results = list(endpoint.filter(name=name))
        obj = results[0] if results else None
    if obj:
        label = slug or name or model
        print(f"  Exists: {label}")
        return obj
    # Build create payload — device types use 'model' instead of 'name'
    create_kwargs = {k: v for k, v in dict(slug=slug, name=name, model=model, **kwargs).items() if v is not None}
    obj = endpoint.create(**create_kwargs)
    print(f"  Created: {obj}")
    return obj


# ── 1. Custom Fields ──────────────────────────────────────────────────────────

print("\n[1] Custom fields")
for cf_name in ("transport", "cli_style"):
    existing = list(nb.extras.custom_fields.filter(name=cf_name))
    if existing:
        print(f"  Exists: {cf_name}")
    else:
        nb.extras.custom_fields.create(
            name=cf_name,
            label=cf_name.replace("_", " ").title(),
            type="text",
            object_types=["dcim.device"],
        )
        print(f"  Created: {cf_name}")


# ── 2. Manufacturer ───────────────────────────────────────────────────────────

print("\n[2] Manufacturer")
cisco = get_or_create(nb.dcim.manufacturers, slug="cisco", name="Cisco")


# ── 3. Device Types ───────────────────────────────────────────────────────────

print("\n[3] Device types")
iol_type = get_or_create(
    nb.dcim.device_types,
    slug="cisco-iol",
    model="Cisco IOL",
    manufacturer=cisco.id,
)
c8kv_type = get_or_create(
    nb.dcim.device_types,
    slug="cisco-c8000v",
    model="Cisco C8000v",
    manufacturer=cisco.id,
)


# ── 4. Platform ───────────────────────────────────────────────────────────────

print("\n[4] Platform")
# Slug MUST be 'cisco_iosxe' — core/netbox.py reads dev.platform.slug
platform = get_or_create(
    nb.dcim.platforms,
    slug="cisco_iosxe",
    name="Cisco IOS-XE",
    manufacturer=cisco.id,
)


# ── 5. Device Roles ───────────────────────────────────────────────────────────

print("\n[5] Device roles")
roles = {}
for slug, name in [
    ("access",       "Access"),
    ("core-abr",     "Core ABR"),
    ("edge-asbr",    "Edge ASBR"),
    ("isp-edge",     "ISP Edge"),
    ("remote-asbr",  "Remote ASBR"),
]:
    roles[slug] = get_or_create(nb.dcim.device_roles, slug=slug, name=name)


# ── 6. Sites ──────────────────────────────────────────────────────────────────

print("\n[6] Sites")
# Names MUST match exactly — core/netbox.py reads dev.site.name
sites = {}
for slug, name in [
    ("access",  "Access"),
    ("core",    "Core"),
    ("edge",    "Edge"),
    ("isp-a",   "ISP A"),
    ("isp-b",   "ISP B"),
    ("remote",  "Remote"),
]:
    sites[name] = get_or_create(nb.dcim.sites, slug=slug, name=name)


# ── 7. Devices ────────────────────────────────────────────────────────────────

print("\n[7] Devices")

DEVICE_DATA = [
    # name,  device_type,  role_slug,      site_name,  transport,   ip
    ("A1C",  iol_type,  "access",       "Access",   "asyncssh",  "172.20.20.205/24"),
    ("A2C",  iol_type,  "access",       "Access",   "asyncssh",  "172.20.20.206/24"),
    ("C1C",  c8kv_type, "core-abr",     "Core",     "restconf",  "172.20.20.207/24"),
    ("C2C",  c8kv_type, "core-abr",     "Core",     "restconf",  "172.20.20.208/24"),
    ("E1C",  c8kv_type, "edge-asbr",    "Edge",     "restconf",  "172.20.20.209/24"),
    ("E2C",  c8kv_type, "edge-asbr",    "Edge",     "restconf",  "172.20.20.210/24"),
    ("IAN",  iol_type,  "isp-edge",     "ISP A",    "asyncssh",  "172.20.20.220/24"),
    ("IBN",  iol_type,  "isp-edge",     "ISP B",    "asyncssh",  "172.20.20.230/24"),
    ("X1C",  c8kv_type, "remote-asbr",  "Remote",   "restconf",  "172.20.20.240/24"),
]

for name, dtype, role_slug, site_name, transport, ip_addr in DEVICE_DATA:
    print(f"\n  Device: {name}")

    # Get or create device
    existing = list(nb.dcim.devices.filter(name=name))
    if existing:
        device = existing[0]
        print(f"    Exists — reusing")
    else:
        device = nb.dcim.devices.create(
            name=name,
            device_type=dtype.id,
            role=roles[role_slug].id,
            site=sites[site_name].id,
            platform=platform.id,
            status="active",
            custom_fields={"transport": transport, "cli_style": "ios"},
        )
        print(f"    Created device")

    # Update custom fields if device already existed (in case they weren't set)
    current_cf = dict(device.custom_fields or {})
    if current_cf.get("transport") != transport or current_cf.get("cli_style") != "ios":
        device.update({"custom_fields": {"transport": transport, "cli_style": "ios"}})
        print(f"    Updated custom fields")

    # Get or create management interface
    ifaces = list(nb.dcim.interfaces.filter(device_id=device.id, name="Management0"))
    if ifaces:
        iface = ifaces[0]
        print(f"    Interface Management0 exists")
    else:
        iface = nb.dcim.interfaces.create(
            device=device.id,
            name="Management0",
            type="virtual",
        )
        print(f"    Created interface Management0")

    # Get or create IP address, assigned to this interface
    existing_ips = list(nb.ipam.ip_addresses.filter(address=ip_addr))
    if existing_ips:
        ip = existing_ips[0]
        print(f"    IP {ip_addr} exists")
        # Ensure it's assigned to the correct interface
        if ip.assigned_object_id != iface.id:
            ip.update({
                "assigned_object_type": "dcim.interface",
                "assigned_object_id": iface.id,
            })
            print(f"    Reassigned IP to Management0")
    else:
        ip = nb.ipam.ip_addresses.create(
            address=ip_addr,
            status="active",
            assigned_object_type="dcim.interface",
            assigned_object_id=iface.id,
        )
        print(f"    Created IP {ip_addr}")

    # Set device primary_ip4 if not already set
    if not device.primary_ip4 or device.primary_ip4.id != ip.id:
        device.update({"primary_ip4": ip.id})
        print(f"    Set primary_ip4 = {ip_addr}")
    else:
        print(f"    primary_ip4 already correct")


# ── Done ──────────────────────────────────────────────────────────────────────

print("\n" + "=" * 50)
print("Population complete.")
print("\nVerify with:")
print("  PYTHONPATH=/home/mcp/aiNOC python -c \"")
print("  from core.netbox import load_devices")
print("  d = load_devices()")
print(f"  print(f'{len} devices loaded')")
print("  \"")
