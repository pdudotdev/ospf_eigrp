# aiNOC Manual Testing Strategy

End-to-end test scenarios for validating Standalone and On-Call agent functionality.
Run these after significant codebase changes to confirm correct agent behavior.

---

## Prerequisites

- Lab is up (`sudo clab redeploy -t lab.yml`) for each test
- All devices reachable (verify with `./run_tests.sh integration`)
- MCP server running or accessible (check with `claude mcp list`)

---

## Standalone Mode Tests

These tests validate the agent's diagnostic and remediation workflow when a user
submits a network problem description directly at the Claude Code prompt.

Launch with:
```bash
cd /home/mcp/mcp-project
claude
```

---

### ST-001 - OSPF Timer Mismatch (R1A)

**Protocol**: OSPF | **Device**: R1A (Arista EOS) | **Symptom**: Adjacency down

#### Setup (break)

Connect to R1A via eAPI or SSH and apply:
```
interface Ethernet3
  ip ospf dead-interval 7
interface Ethernet4
  ip ospf dead-interval 7
```

#### Verify break

From R1A:
```
show ip ospf neighbor
```
Expected: R2C and R3C are **absent** from Area 0 neighbors (Ethernet3/Ethernet4).

#### Agent prompt
```
OSPF adjacencies are down on R1A. R1A shows no OSPF neighbors in Area 0. Please investigate.
```

#### Expected agent behavior

1. Reads `skills/ospf/SKILL.md`
2. Calls `get_ospf(R1A, "neighbors")` → no Area 0 neighbors
3. Calls `get_ospf(R1A, "interfaces")` → dead-interval 7 on Ethernet3/Ethernet4
4. Identifies timer mismatch (EOS default dead-interval = 40s)
5. Proposes removing the dead-interval override on R1A Ethernet3 and Ethernet4
6. Asks user approval before applying
7. Applies fix, verifies R2C and R3C return to FULL state

#### Verify fix

```
show ip ospf neighbor
```
Expected: R2C and R3C present, state FULL.

#### Teardown (if agent did not fix)

```
interface Ethernet3
  no ip ospf dead-interval
interface Ethernet4
  no ip ospf dead-interval
```

---

### ST-002 - EIGRP Passive Interface (R8C)

**Protocol**: EIGRP | **Device**: R8C (Cisco IOS) | **Symptom**: Neighbor down

#### Setup (break)

SSH to R8C and apply:
```
router eigrp 20
  passive-interface Ethernet0/3
```

#### Verify break

From R8C:
```
show ip eigrp neighbors
```
Expected: R9C is **absent**.

From R9C:
```
show ip eigrp neighbors
```
Expected: R8C is **absent**.

#### Agent prompt
```
R9C has lost EIGRP connectivity. R9C cannot reach any OSPF-learned destinations. Please investigate.
```

#### Expected agent behavior

1. Reads `skills/eigrp/SKILL.md`
2. Calls `get_eigrp(R8C, "neighbors")` → no neighbors
3. Calls `get_eigrp(R8C, "interfaces")` → Ethernet0/3 is passive
4. Proposes removing passive-interface Ethernet0/3 on R8C
5. Asks approval, applies, verifies R9C neighbor returns FULL

#### Verify fix

```
show ip eigrp neighbors
```
On R8C: R9C present. On R9C: R8C present.

#### Teardown (if agent did not fix)

```
router eigrp 20
  no passive-interface Ethernet0/3
```

---

### ST-003 - Redistribution Break (R3C)

**Protocol**: Redistribution | **Device**: R3C (Cisco IOS) | **Symptom**: Routes missing

#### Setup (break)

SSH to R3C and remove OSPF→EIGRP redistribution:
```
router eigrp 10
  redistribute ospf 1 route-map OSPF-TO-EIGRP
```

#### Verify break

From R4C:
```
show ip route
```
Expected: No `D EX` routes for `172.16.0.0/24` (OSPF Area 2 subnet) or other OSPF-originated prefixes.

#### Agent prompt
```
R4C is missing routes to the 172.16.0.0/24 subnet (Area 2 stub network).
Routes that should be redistributed from OSPF into EIGRP AS10 are absent on R4C.
```

#### Expected agent behavior

1. Reads `skills/redistribution/SKILL.md`
2. Calls `get_eigrp` and `get_ospf` tools
3. Calls `get_routing(R4C, "172.16.0.0/24")` → route missing
4. Calls `get_routing_policies(R3C, "redistribution")` → redistribute statement absent
5. Proposes restoring: `redistribute ospf 1 metric 1000 1 255 1 1500` under `router eigrp 10`
6. Asks approval, applies, verifies route returns on R4C

#### Verify fix

From R4C:
```
show ip route 172.16.0.0
```
Expected: `D EX 172.16.0.0/24` present.

#### Teardown (if agent did not fix)

```
router eigrp 10
  redistribute ospf 1 metric 1000 1 255 1 1500
```

---

### ST-004 - Policy-Based Routing Investigation (R8C)

**Protocol**: Routing Policy | **Device**: R8C (Cisco IOS) | **Symptom**: Traffic from R9C to 2.2.2.66 follows asymmetric path

#### Setup (break)

SSH to R8C and apply PBR configuration:
```
ip access-list extended 100
 10 permit ip host 192.168.20.2 host 2.2.2.66
route-map ACCESS-R2-LO permit 10
 match ip address 100
 set ip next-hop 10.1.1.6
interface Ethernet0/3
 ip policy route-map ACCESS-R2-LO
```

#### Verify break

From R9C toward R2A loopback:
```
traceroute 2.2.2.66
```
Expected: Path goes through `10.1.1.6` (R7A), not R6A.

#### Agent prompt

```
Why does R8C forward packets from R9C's 192.168.20.2 interface destined for 2.2.2.66 to R7A every time?
```

#### Expected agent behavior

1. Reads routing policy skills
2. Calls `get_routing(R8C, "2.2.2.66")` → shows normal ECMP paths (R6A 10.1.1.2 and R7A 10.1.1.6 equal cost)
3. Calls `get_routing_policies(R8C, "route_maps")` → finds `ACCESS-R2-LO` with `set ip next-hop 10.1.1.6`
4. Calls `get_routing_policies(R8C, "access_lists")` → finds ACL 100 matching host 192.168.20.2 → host 2.2.2.66
5. Identifies PBR on Et0/3 overriding normal routing decisions
6. Correctly diagnoses root cause with explanation of ACL match and next-hop override
7. No fix or documentation needed, it was just a user question.

#### Verify (diagnostic only)

Agent correctly identified:
- PBR as root cause
- The specific ACL and route-map involved
- The forced next-hop (10.1.1.6 = R7A)

#### Teardown (if agent did not fix, restore clean state)

N/A

---

### ST-005 - EIGRP Stub/Summary Misconfiguration (R9C)

**Protocol**: EIGRP | **Device**: R9C (Cisco IOS) | **Symptom**: Individual loopback /24 routes advertised instead of /22 summary

#### Setup (break)

SSH to R9C and change stub from `connected summary` to `connected`:
```
router eigrp 20
  eigrp stub connected
```

#### Verify break

From R1A:
```
show ip route | include 9.9
```
Expected: Three separate `O E1 9.9.x.0/24` entries visible instead of a single `O E1 9.9.0.0/22`.

#### Agent prompt

```
Why are all routers in the network (e.g. R1A) showing individual routes to R9C's loopbacks.
Check this and give me all potential fixes to choose from.
```

#### Expected agent behavior

1. Reads `skills/eigrp/SKILL.md`
2. Calls `get_routing()` and/or `get_routing_policies` 
3. Calls `get_eigrp(R9C, "config")` → finds `eigrp stub connected` (no `summary` keyword)
4. Calls `get_eigrp(R9C, "interfaces")` → identifies summary-address on Et0/1
5. Identifies conflict: stub `connected` without `summary` overrides and advertises individual connected routes
6. Presents multiple fix options (change stub to include `summary`, modify interface summary, summarize at R8C, etc.)
7. User selects Option that configures `eigrp stub summary` on R9C
8. Applies fix, verifies /22 summary now present and individual /24s suppressed on R1A

#### Verify fix

```
show ip route | include 9.9
```
Expected: Single `O E1 9.9.0.0/22` present.

#### Teardown (if agent did not fix)

```
router eigrp 20
  eigrp stub connected summary
```

---

## On-Call Mode Tests

These tests validate the full watcher → agent pipeline. The watcher monitors
`/var/log/network.json`, detects SLA Down events, and spawns a Claude agent session.

### Setup for all On-Call tests

In a separate terminal, start the watcher:
```bash
cd /home/mcp/mcp-project
python3 oncall_watcher.py
```

Also monitor `/var/log/network.json`:
```bash
tail -f /var/log/network.json
```

Monitor the watcher log in another terminal:
```bash
tail -f /home/mcp/mcp-project/oncall_watcher.log
```

Generate real IP SLA path failures for On-Call tests.

---

### OC-001 - OSPF Passive Interface → R4C/R9C SLA Failure

**SLA Path**: `R4C_TO_R10C` | **Break device**: R3C | **SLA source**: R4C (172.20.20.204)
**Implicit**: `R9C_TO_R5C` | R3C failure breaks two SLA paths at once

#### Setup (break)

SSH to R3C:
```
router ospf 1
  passive-interface Ethernet0/3
  passive-interface Ethernet1/0
```

#### Verify break

From R3C:
```
show ip ospf neighbor
```
Expected: R1A (via Ethernet0/3) **absent**.
Expected: R2C (via Ethernet1/0) **absent**.

From R4C:
```
show ip route 10.10.10.10
```
Expected: Route to R10C loopback `10.10.10.10` **absent**.

#### Check /var/log/network.json

Two IP SLA paths failed as a result of the misconfiguration above:
```
{"device":"172.20.20.204","facility":"local7","msg":"BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down","severity":"info","ts":"2026-02-25T07:26:05.065Z"}
{"device":"172.20.20.209","facility":"local7","msg":"BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down","severity":"info","ts":"2026-02-25T07:26:09.841Z"}
```

#### Check oncall_watcher.log

Agent starts working on the first failure (reported by R4C):
```
[2026-02-25 07:26:06 UTC] Agent invoked for event on R4C: BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down
```
Claude Code session opens automatically in the terminal where `oncall_watcher.log` runs.

#### Expected agent behavior

1. Reads `skills/oncall/SKILL.md`
2. Looks up `R4C_TO_R10C` in `sla_paths/paths.json` → scope: R4C, R3C, R1A, R10C
3. Traceroutes from R4C to `10.10.10.10` → stops at R3C
4. Reads `skills/ospf/SKILL.md`
5. Calls `get_ospf(R3C, "neighbors")` → R1A missing
6. Calls `get_ospf(R3C, "config")` → passive-interface on Ethernet0/3 and Ethernet1/0
7. Proposes removing passive-interface on R3C Ethernet0/3 and Ethernet1/0
8. Asks user approval (displayed in the agent session)
9. Applies fix, verifies R4C route to 10.10.10.10 returns
10. Asks user to document case inside `cases.md`
11. If step 10 is approved, adds new lesson to `lessons.md`

**NOTE: Keep the session open and see step 12 below after verifying the fix!**

#### Verify fix

From R3C:
```
show ip ospf neighbor
```
Expected: R1A and R2C FULL.

In `/var/log/network.json`:
```
{"device":"172.20.20.204","facility":"local7","msg":"BOM%TRACK-6-STATE: 1 ip sla 1 reachability Down -> Up","severity":"info","ts":"2026-02-25T07:33:45.102Z"}
```

From R4C:
```
show ip route 10.10.10.10
```
Expected: Route present via OSPF/EIGRP redistribution path.

```
show ip sla statistics
```
Expected: Latest operation return code: OK

#### Documentation check

- New case in `cases/cases.md` with R4C context
- `Verification: PASSED`
- `Case Status: FIXED`

#### Teardown (if agent did not fix)

```
router ospf 1
  no passive-interface Ethernet0/3
  no passive-interface Ethernet1/0
```

#### Deferred Event Handling (Storm Prevention)

**Purpose**: Validate that concurrent SLA events during an active session are deferred
and surfaced in a follow-up review session.

**Reason**: The R3C passive-interface configurations broke two SLA paths:
- R4C to R10C
- R9C to R5C

**NOTE:** The agent is invoked for the **first failure only**. If a second failure occurs during the investigation of the first one, agent skips it - this avoids any agent storms during outages, thus preventing chaotic config changes on multiple devices and increased API costs.

12. After the fix for the first failure is applied and documentation written, type `/exit`
13. Check second event logged as: `SKIPPED (deferred - occurred during active session) - R9C (...)` in `oncall_watcher.log`:
```
[2026-02-25 07:53:52 UTC] SKIPPED (deferred - occurred during active session) - R9C (172.20.20.209): BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down
```
14. After first agent session closes (user types `/exit`), a **second agent session** opens automatically with the deferred review prompt listing the R9C failure.
```
During the previous On-Call session the following SLA path failures were detected but could not be investigated at the time (logged as SKIPPED in oncall_watcher.log):

1. R9C (172.20.20.209): BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down (at 2026-02-25T07:26:09.841Z)

Would you like to investigate any of these? Reply with a number, 'all', or 'none'.

- Number or 'all': I'll investigate using the full On-Call workflow, document the case in cases/cases.md, curate cases/lessons.md, and return to the deferred list for any remaining failures.
- 'none': Type /exit to close this review session.
```
15. If multiple SLA path failures occured during the initial investigation, they will be listed here and the user can choose a number to investigate a specific issue, or `/exit` to exit.
16. If the user enters `/exit`, then the agent quits and the monitoring process resumes automatically to listen for new issues:
```
[Watcher] Deferred review session ended. Resuming monitoring
```

---

## Watcher Behavior Validation

These checks can be done without breaking lab config.

### WB-001 - Non-SLA Events Are Ignored

Inject a syslog message that is NOT an SLA Down event:
```bash
echo '{"ts":"2026-01-01T00:00:00Z","device":"172.20.20.201","msg":"%SYS-5-CONFIG_I: Configured from console"}' >> /var/log/network.json
```
Expected: Watcher does **not** invoke agent. Log shows no new `Agent invoked` entry.

### WB-002 - SLA Up Events Are Ignored

```bash
echo '{"ts":"2026-01-01T00:00:00Z","device":"172.20.20.204","msg":"%TRACK-6-STATE: 1 ip sla 1 reachability Down -> Up"}' >> /var/log/network.json
```
Expected: No agent invocation. (Only `Down` transitions trigger.)

### WB-003 - MikroTik Netwatch Event Detected

```bash
echo '{"ts":"2026-01-01T00:00:00Z","device":"172.20.20.218","msg":"netwatch,info event down [ type: simple, host: 10.0.0.1 ]"}' >> /var/log/network.json
```
Expected: Watcher **does** invoke agent (MikroTik format matched).

---

## Case Documentation Checks

After any Standalone or On-Call test run:

1. **New case added to cases.md**:
Check the last `📄 CASE NO.` in the file, e.g. `CASE NO. - 00019-R4C-SLA`

2. **Case contains required fields**:
All fields described in `case_format.md` are present.

3. **Lessons learned** (optional, check if lessons.md was updated):

---

## Maintenance Window Policy

The agent must refuse config pushes outside the maintenance window defined in
`policy/MAINTENANCE.json` (UTC Mon–Fri 05:00–20:00).

### MW-001 - Change Blocked Outside Window

To test this, temporarily edit the maintenance window to exclude the current time
(or run this test after 20:00 UTC on a weekday / any time on weekend).

Apply a break, submit a Standalone prompt, and confirm:
- Agent diagnoses the issue correctly
- Agent proposes the fix
- When user approves, `push_config` returns an error about maintenance window
- Agent reports the block to the user without retrying

**Do not modify `MAINTENANCE.json` permanently** - restore after testing.