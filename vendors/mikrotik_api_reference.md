# MikroTik RouterOS REST API Reference

> Verified on RouterOS 7.20.8 (long-term). Applies to all `cli_style="routeros"` devices.

## Config Push Format

`push_config` commands for RouterOS devices must be JSON-encoded REST action strings (not CLI commands). Each command takes the form:
```
'{"method": "PATCH", "path": "/rest/routing/ospf/interface/<id>", "body": {"area": "0.0.0.0"}}'
```

Always use protocol tools (`get_ospf`, `get_bgp`, etc.) to discover RouterOS resource IDs before issuing PATCH or DELETE — these tools return the `.id` field needed for targeted updates.

## Method Mapping

| HTTP Method | RouterOS Action | Target Path | Example |
|-------------|----------------|-------------|---------|
| `PUT` | Create (add) | Collection path | `PUT /rest/interface/bridge` |
| `PATCH` | Modify (set) | Item path with `/<id>` | `PATCH /rest/interface/bridge/*7` |
| `DELETE` | Remove | Item path with `/<id>` | `DELETE /rest/interface/bridge/*7` |
| `GET` | Read (print) | Collection or item path | `GET /rest/ip/address` |

> **Do NOT use POST** for resource creation — RouterOS returns "no such command" (400). Use `PUT` instead.

## Common Write Operation Paths

| Operation | Method | Path | Body Example |
|-----------|--------|------|-------------|
| Create bridge (loopback) | PUT | `/rest/interface/bridge` | `{"name": "lo2", "comment": "Loopback2"}` |
| Add IP address | PUT | `/rest/ip/address` | `{"address": "10.0.0.1/24", "interface": "lo2"}` |
| Remove IP address | DELETE | `/rest/ip/address/<id>` | — |
| Modify OSPF interface | PATCH | `/rest/routing/ospf/interface/<id>` | `{"cost": "10"}` |
| Create OSPF area | PUT | `/rest/routing/ospf/area` | `{"name": "area1", "area-id": "0.0.0.1", "instance": "default"}` |
| Add OSPF interface template | PUT | `/rest/routing/ospf/interface-template` | `{"interfaces": "lo2", "area": "backbone"}` |
| Modify BGP connection | PATCH | `/rest/routing/bgp/connection/<id>` | `{"disabled": "true"}` |
| Create static route | PUT | `/rest/ip/route` | `{"dst-address": "10.0.0.0/8", "gateway": "192.168.1.1"}` |
| Delete static route | DELETE | `/rest/ip/route/<id>` | — |
| Modify interface | PATCH | `/rest/interface/<id>` | `{"disabled": "true"}` |
