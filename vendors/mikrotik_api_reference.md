# MikroTik RouterOS REST API Reference

> Verified on RouterOS 7.20.8 (long-term). Applies to all `cli_style="routeros"` devices.

## Config Push Format

`push_config` commands for RouterOS devices must be JSON-encoded REST action strings (not CLI commands). Each command takes the form:
```
'{"method": "PATCH", "path": "/rest/routing/ospf/interface-template/<id>", "body": {"hello-interval": "10s"}}'
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
| Modify OSPF interface template | PATCH | `/rest/routing/ospf/interface-template/<id>` | `{"hello-interval": "10s"}` |
| Create OSPF area | PUT | `/rest/routing/ospf/area` | `{"name": "area1", "area-id": "0.0.0.1", "instance": "default"}` |
| Add OSPF interface template | PUT | `/rest/routing/ospf/interface-template` | `{"interfaces": "lo2", "area": "backbone"}` |
| Modify BGP connection | PATCH | `/rest/routing/bgp/connection/<id>` | `{"disabled": "true"}` |
| Create static route | PUT | `/rest/ip/route` | `{"dst-address": "10.0.0.0/8", "gateway": "192.168.1.1"}` |
| Delete static route | DELETE | `/rest/ip/route/<id>` | — |
| Modify interface | PATCH | `/rest/interface/<id>` | `{"disabled": "true"}` |

> **OSPF interfaces are read-only — always use interface-template for config changes.** Entries at `/rest/routing/ospf/interface` (returned by `get_ospf(device, "interfaces")`) are auto-created by the OSPF process and marked `dynamic: true`. PATCHing them returns HTTP 400. To modify timers (hello-interval, dead-interval), cost, or other interface-level OSPF parameters, target `/rest/routing/ospf/interface-template/<id>` instead. Discover template IDs with `run_show(device, '{"method": "GET", "path": "/rest/routing/ospf/interface-template"}')`.
