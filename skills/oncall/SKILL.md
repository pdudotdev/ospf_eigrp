---
name: On-Call SLA Troubleshooting
description: "SLA path failure workflow — read sla_paths.json, traceroute-first localization, ECMP handling, protocol triage"
---

# On-Call SLA Troubleshooting Skill

## Scope
On-Call mode investigation guide — reading sla_paths.json, traceroute-first localization, ECMP handling, protocol triage order.

---

## Step 0: Read the sla_paths.json Entry for the Failed Path

Use the **Read** tool to read the file `sla_paths/paths.json` (this is a local file — do NOT use `readMcpResource`).

Locate the path entry matching the source device from the log event. Extract these key fields:

- **`source_device`**: the device that generated the SLA failure event
- **`destination_ip`**: IP being pinged by the SLA
- **`scope_devices`**: ALL devices you may need to investigate
- **`ecmp`**: if true, TWO paths exist — both must be checked
- **`ecmp_node`**: the device where the path splits
- **`ecmp_next_hops`**: the two next-hop devices after the split

---

## Step 1: Traceroute from Source Device (Always First)

If `source_ip` is available in the paths.json entry, always pass it:

```
traceroute(device=<source_device>, destination=<destination_ip>, source=<source_ip>)
```

Using `source_ip` forces the traceroute onto the monitored path. If the source interface is down, the traceroute fails immediately at R10C — correctly localizing the issue without alternate-path confusion.

Read the output:

- **Path stops at hop N (or fails at source)**: issue is on or before that hop → proceed to Step 2.5
- **Timeout at first hop**: issue is on the source device itself (interface down, EIGRP/OSPF neighbor lost, no default route) → proceed to Step 2.5
- **Path transits a device NOT in scope_devices**: routing anomaly on the last in-scope hop. Do NOT investigate the off-path device. Identify the last hop that IS in scope_devices, run `get_routing(<that_device>, prefix=<destination_ip>)` to confirm it is routing toward the off-path device. Whether the route is present or absent, treat that in-scope device as the breaking hop and proceed immediately to Step 2.5.
- **Full path to destination**: do NOT conclude "transient" yet — go to Step 1a

### Step 1a: Source-Device Sanity Check (when traceroute succeeds)

Even if the traceroute completes, the SLA was triggered for a reason. Verify the source device's local state with exactly two queries:

```
get_interfaces(device=<source_device>)
get_ospf(device=<source_device>, query="neighbors")   ← run on source_device, NOT the next-hop
```

> **Critical**: Always query routing protocol neighbors on the **source_device** first. Querying the next-hop device may show healthy adjacencies even when the source-side interface is down.

**Branch A — Appears Recovered** (source interface Up/Up AND all expected neighbors present):

Present this summary table and ask the user before doing anything else:

```
| Check | Result | Status |
|-------|--------|--------|
| Traceroute to <destination_ip> | Full path, all hops respond | ✓ |
| Source interface (<source_interface>) | Up/Up | ✓ |
| Routing protocol neighbors on <source_device> | All expected neighbors present | ✓ |

The SLA path appears to have recovered. Likely cause: transient condition
(brief routing instability, probe timing) now resolved.

What would you like to do?
  A) Document as resolved (transient/recovered) and close the case
  B) Run deeper diagnostics (interface error counters, neighbor state history)
  C) Return to the deferred SLA list / exit without investigating further
```

- If user picks **A**: proceed to session closure (Jira will be updated and lessons evaluated per CLAUDE.md On-Call Session Closure).
- If user picks **B**: proceed to Step 2.5 on the source device, then Step 3 if neighbors are healthy.
- If user picks **C**: proceed to session closure (log to Jira as transient/self-resolved, evaluate lessons per CLAUDE.md On-Call Session Closure).
- **Do NOT proceed to Step 3 without the user explicitly requesting it** — unnecessary investigation wastes time and cost.

**Branch B — Issue still present** (source interface down OR expected neighbor missing):

This is the root cause. Proceed directly to Step 2.5.

---

## Step 2: ECMP Handling

If `ecmp=true`, the traceroute shows ONE of the two paths. The other path may also be broken.

After fixing one path, verify the ECMP node still has both paths:

```
get_routing(ecmp_node, prefix=<destination or next_hop>)   → expect 2 equal-cost entries
```

---

## Step 2.5: Basic Operational Checks (Mandatory — Run Before Anything Else)

**A missing route on the breaking hop is NOT a reason to investigate other devices.**
It is a reason to check the breaking hop's own state first.

```
get_interfaces(device=<breaking_hop>)
get_ospf(device=<breaking_hop>, query="neighbors")    ← or get_eigrp / get_bgp per Step 3 triage table
```

**Decision gate:**

| Result | Action |
|--------|--------|
| Interface down (admin or line-protocol) | Root cause found. Present findings table. Stop. |
| No neighbors / fewer neighbors than expected | Go directly to the **Adjacency Checklist** in the protocol skill. Do NOT investigate downstream devices. |
| All neighbors FULL, all interfaces Up/Up | Proceed to Step 3. Issue is in LSDB, RIB, or policy layer. |

> **Do not leave the breaking hop to investigate R5C, R8C, or other devices in the path.**
> Missing adjacencies on the breaking hop explain missing routes everywhere downstream.
> Investigating downstream only confirms the problem cascaded — it never finds the root cause.
> Timer mismatch, passive interface, and area mismatch are caught in one query.

---

## Step 3: Protocol Triage — Which Skill to Read Next

Map the breaking hop to its protocol:

| Breaking Hop Device | Protocol to Investigate | Skill to Read |
|--------------------|------------------------|---------------|
| R9C (source) | EIGRP AS20 (to R8C) | `skills/eigrp/SKILL.md` |
| R8C | EIGRP AS20 neighbor + OSPF Area1 + bidirectional redistribution | `skills/eigrp/SKILL.md`, `skills/ospf/SKILL.md`, and if redistributed routes are missing: `skills/redistribution/SKILL.md` |
| R6A, R7A | OSPF Area1 NSSA | `skills/ospf/SKILL.md` |
| R4C, R5C (source) | EIGRP AS10 (to R3C) | `skills/eigrp/SKILL.md` |
| R3C | OSPF Area0 / EIGRP AS10 / Redistribution / BGP | Traceroute direction matters: inbound from R4C/R5C side → `skills/eigrp/SKILL.md`; outbound toward R1A/R2C → `skills/ospf/SKILL.md`; toward ISP → `skills/bgp/SKILL.md`; redistributed routes missing → `skills/redistribution/SKILL.md` |
| R2C | OSPF Area0 (to R1A/R3C) / OSPF ABR Area1 NSSA (to R6A/R7A) / BGP | If OSPF neighbors down → `skills/ospf/SKILL.md`; if BGP to ISP down → `skills/bgp/SKILL.md`. Note: R2C has no EIGRP. |
| R1A | OSPF ABR (Areas 0↔2) | `skills/ospf/SKILL.md` |
| R10C, R11C (as source or breaking hop) | OSPF Area2 stub (adjacency to R1A, default route from ABR) | `skills/ospf/SKILL.md` |
| R12C (ISP A edge / RR) | BGP | `skills/bgp/SKILL.md` |
| R13C, R14C, R15C (ISP A transit/core) | Outside our admin domain — not in scope_devices for any SLA path. If traceroute transits through them and stops, verify eBGP session to R12C and escalate to ISP A. | `skills/bgp/SKILL.md` (eBGP to R12C only) |
| R16C, R17C (ISP B edge) | BGP | `skills/bgp/SKILL.md` |
| R18M, R19M (source) | OSPF Area0 (London) / BGP | `skills/ospf/SKILL.md` or `skills/bgp/SKILL.md` |

---

## Time Efficiency Rules

- **Localize first, don't investigate all**: traceroute narrows to 1-2 devices max before running protocol tools
- **ECMP: check both paths** before concluding the issue is fixed
- **Don't re-check devices that are not on the scope_devices list**: out-of-scope devices won't affect this SLA path
- **Non-scope hop in traceroute: stay in scope**: if traceroute exits scope_devices, do NOT query or investigate the off-path device. Find the last in-scope hop, run `get_routing` on it, then go to Step 2.5.
- **No route on breaking hop → check its neighbors, not downstream devices**: a missing route means "run Step 2.5 on this device now" — not "go check R5C/R8C to trace the gap". Missing adjacencies on the breaking hop explain missing routes across the entire downstream path.
- **Step 2.5 before any protocol skill section**: zero neighbors is an adjacency problem (timers, passive, area, auth). Resolve it on the breaking hop before consulting LSDB, redistribution, or area-type sections.

---

## Presenting Findings

Always present your analysis summary in a Markdown table before proposing a fix:

| Finding | Detail | Status |
|---------|--------|--------|
| Traceroute result | Stopped at hop N — device X | ✗ |
| Interface / neighbor state | e.g. Ethernet3 admin down | ✗ |
| Root cause | Brief description | ✗ |

Use ✓ for healthy items and ✗ for the identified issues. This lets the user scan the summary instantly before approving any configuration change.

---

## Jira Updates (On-Call)

If a Jira issue key was provided in the invocation prompt, use the structured format from `cases/case_format.md` for all Jira comments. This ensures consistent, professional case records in Jira.

**After presenting the findings table:**
```
jira_add_comment(issue_key=<key>, comment=<structured comment using case_format.md>)
```
Include: Reported Issue, All Commands Used To Isolate Issue, Commands That Actually Identified the Issue, and the findings table with ✓/✗ status markers.

**After fix is verified PASSED:**
```
jira_resolve_issue(issue_key=<key>, resolution_comment=<structured resolution>, resolution="Done")
```
Include: Proposed Fixes (Per Device), Commands Used Upon User Approval, Post-Fix State, Verification result.

**If fix is declined by operator:**
```
jira_add_comment(issue_key=<key>, comment=<structured comment with proposed fix details>)
```
Include: "Proposed fix was declined by operator. Issue remains open." followed by what was proposed and why. Do NOT resolve the ticket.

**For transient/recovered (no fix applied):**
```
jira_resolve_issue(issue_key=<key>, resolution_comment=<brief summary>, resolution="Won't Fix")
```

If Jira is not configured, these tools return a skip notice — continue without them.
