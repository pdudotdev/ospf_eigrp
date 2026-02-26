---
name: Routing Policy & Path Selection
description: "Path selection investigation — PBR, route-map and prefix-list policy influence, ECMP behavior, routing table verification"
---

# Routing Policy & Path Selection Skill

## Scope
Path selection troubleshooting for all devices. Read this skill when traffic takes an unexpected or consistently asymmetric path and protocol adjacency/route presence are confirmed correct. PBR (`policy_based_routing` query) is **ios-only**.

## Start Here: Policy Check Sequence

When traffic consistently takes an unexpected path, check in this order — do not skip steps:

    get_routing_policies(device, "policy_based_routing")   ← ios only; skip for eos/routeros
    get_routing_policies(device, "route_maps")
    get_routing_policies(device, "prefix_lists")
    get_routing(device, prefix="<destination>")

> **PBR must be checked before any protocol cost math.** PBR overrides the routing table entirely — OSPF, EIGRP, and BGP best-path calculations are irrelevant if a `ip policy route-map` is applied on the ingress interface.

| Finding | Root Cause |
|---------|-----------|
| Interface has `ip policy route-map X` | PBR is active — inspect the route-map and ACL before anything else |
| Route-map `set metric` biasing a redistributed path | Redistribution policy is skewing path preference → see `skills/redistribution/SKILL.md` |
| Prefix-list `deny` at a redistribution or distribution point | Route blocked from being advertised upstream — missing from downstream RIBs |
| Single RIB entry when two equal-cost paths are expected | PBR, cost asymmetry, `maximum-paths 1`, or distribute-list filtering |
| Two equal-cost RIB entries but one path always selected | Normal CEF per-destination hashing — not a Router ID tie-breaker |

---

## Symptom: Policy-Based Routing

`policy_based_routing` returns only the **interface binding** — which interface has `ip policy route-map X` applied. It does not show the route-map logic. Always follow with two more queries:

    get_routing_policies(device, "policy_based_routing")   → identifies which interface has PBR
    get_routing_policies(device, "route_maps")             → shows match/set clauses for that route-map
    get_routing_policies(device, "access_lists")           → shows ACL referenced in the match clause (ios/eos only)

### What to look for in route-map output

- `match ip address <ACL>` — which traffic is matched (source/destination criteria)
- `set ip next-hop <IP>` — matched traffic is forwarded here, bypassing the RIB
- `set interface <intf>` — matched traffic exits a specific interface regardless of routing
- `deny` sequence with no `set` — traffic in a deny sequence falls through to the RIB (not PBR-forwarded)

> **Never conclude "PBR is not the cause" from `policy_based_routing` alone.** If an interface shows `ip policy`, always fetch both `route_maps` and `access_lists` before forming a conclusion. The three queries work as a chain: binding → logic → match criteria.

---

## Symptom: Route Filtering by Route Map or Prefix List

Route-maps applied at redistribution points can modify metrics, biasing path preference on downstream devices. Prefix-lists used as distribute-lists or in redistribution route-maps can block routes from being accepted into or advertised from the RIB — making them absent on downstream routers.

    get_routing_policies(device, "route_maps")     → check for set metric or deny sequences
    get_routing_policies(device, "prefix_lists")   → check permit/deny entries for the affected prefix
    get_ospf(device, "config")                     → check for distribute-list under router ospf
    get_eigrp(device, "config")                    → check for distribute-list under router eigrp

**Direction matters:** filters are applied either inbound (blocking routes from entering the local RIB from a neighbor/protocol) or outbound (blocking routes from being advertised). The filter is configured on the device doing the filtering — the downstream device is where the route will be absent.

**Implicit deny:** every prefix-list ends with an implicit `deny any`. Routes not explicitly permitted are silently dropped.

> For route-map filtering on `redistribute` statements (seed metrics, loop prevention, `subnets` keyword), see `skills/redistribution/SKILL.md`. For BGP attribute manipulation (`set local-preference`, `set weight`, `set as-path prepend`), see `skills/bgp/SKILL.md` — Wrong Best Path section.

---

## Symptom: ECMP — Traffic Always Takes One Path

When two equal-cost paths are expected but traffic consistently uses the same one:

    get_routing(device, prefix="<destination>")   → must show 2+ equal-cost entries for true ECMP
    traceroute(device, destination="<dest>")      → confirms actual forwarding path for that flow

| RIB result | Interpretation |
|-----------|---------------|
| Two entries, equal cost | True ECMP. CEF uses per-destination hashing — a single src/dst IP pair always takes the same path. This is normal, not a misconfiguration. |
| One entry only | ECMP never established — investigate below. |

> **On Cisco IOS with CEF, per-destination load balancing means a single flow always takes the same path.** This is deterministic CEF hashing of the src/dst IP pair — it is NOT a Router ID tie-breaker. Attributing consistent path selection to "higher Router ID wins" is incorrect for IOS OSPF ECMP.

If only one path is installed when two are expected:

1. **Check cost symmetry** — unequal costs mean only the better path is installed:

        get_ospf(device, "database")     → compare LSA costs on both candidate paths
        get_eigrp(device, "topology")    → compare FD values for both paths

2. **Check `maximum-paths`** — default is 4 on IOS-XE for both OSPF and EIGRP; if set to 1, only one path installs:

        get_ospf(device, "config")       → look for maximum-paths under router ospf
        get_eigrp(device, "config")      → look for maximum-paths under router eigrp

3. **Check PBR** — a route-map on the ingress interface can force one path regardless of the RIB:

        get_routing_policies(device, "policy_based_routing")   ← ios only

---

## Symptom: NAT/PAT Translation Issues

> **Low priority** — only investigate NAT after all routing, adjacency, and policy checks pass. NAT issues are rare root causes in this network.

When the breaking hop is a **NAT_EDGE** device (R2C, R3C, R18M, R19M per INTENT.json) and all of the following are true:
- All interfaces Up/Up
- All protocol neighbors FULL
- Routes present in RIB with correct next-hops
- No PBR, route-map, or prefix-list anomalies

Then check NAT translations:

    get_routing_policies(device, "nat_pat")

### Cisco IOS (R2C, R3C) — PAT mode
`show ip nat translation` returns the active translation table.

| Finding | Root Cause |
|---------|-----------|
| Empty translation table | No traffic is being NATed — check `ip nat inside`/`ip nat outside` interface designations and NAT ACL/route-map |
| Translations present but destination unreachable | NAT is working; issue is upstream (ISP) or return-path related |
| Only inside→outside entries, no outside→inside | One-way NAT — return traffic may be blocked by ISP or missing reverse route |

Also verify NAT interface designations:

    run_show(device, "show ip nat statistics")

Look for: inside/outside interface counts, active translations, expired translations, and pool exhaustion.

### MikroTik RouterOS (R18M, R19M) — Masquerade mode
The REST endpoint `/rest/ip/firewall/nat` returns NAT rules.

| Finding | Root Cause |
|---------|-----------|
| No masquerade rule present | NAT not configured — traffic exits with private source IP, ISP drops it |
| Masquerade rule disabled | Same as above — rule exists but is not active |
| Rule present and enabled, out-interface correct | NAT is working; issue is upstream |

---

## Query Reference

| Query | What it returns | Platform support |
|-------|----------------|-----------------|
| `policy_based_routing` | Interfaces with `ip policy route-map X` applied | **ios only** |
| `route_maps` | All route-map definitions (match/set clauses, sequences) | ios, eos, routeros |
| `prefix_lists` | Prefix-list definitions (permit/deny per range) | ios, eos, routeros |
| `access_lists` | ACL definitions — used to identify PBR match criteria | ios, eos only |
| `redistribution` | Active redistribution statements | ios, eos only |
| `nat_pat` | NAT/PAT translations (ios) or firewall NAT rules (routeros) | ios, eos, routeros — **NAT_EDGE devices only** |

---

## Verification Checklist (Post-Fix)

- [ ] `get_routing_policies(device, "policy_based_routing")` — no unexpected `ip policy` bindings on ingress interfaces (ios only)
- [ ] `get_routing_policies(device, "route_maps")` — no `deny` sequences or `set metric` clauses unexpectedly biasing the path
- [ ] `get_routing_policies(device, "prefix_lists")` — affected prefix is covered by `permit`, not `deny`
- [ ] `get_routing(device, prefix="<destination>")` — correct number of next-hops installed in RIB
- [ ] `traceroute(device, destination="<dest>")` — actual forwarding path matches expected topology
- [ ] `get_routing_policies(device, "nat_pat")` — if NAT_EDGE device: translations present and NAT rules active (check only when relevant)
