# aiNOC Manual Testing Strategy

End-to-end test scenarios for validating On-Call agent functionality.
Run these after significant codebase changes to confirm correct agent behavior.

---

## When to Run What

### Tier 1 — Core Regression (~2 min) | Run after every change

Run automated tests first:
```bash
cd /home/mcp/aiNOC/testing/agent-testing
./run_tests.sh unit         # run only unit tests
./run_tests.sh integration  # requires running lab
./run_tests.sh all          # run unit and integration
```

Then these manual scenarios:
- **WB-004** — Service Mode (primary deployment mode — always test in service mode)
- **OC-001** — Full On-Call Pipeline (Primary Setup + Deferred)

### Tier 2 — Targeted (~15 min) | Run when touching related code

- **WB-004** — Watcher Behavior edge cases (service mode sub-scenarios not covered in Tier 1)

---

## Prerequisites

- Lab is up (`sudo clab redeploy -t AINOC-TOPOLOGY.yml`) for each test
- All devices reachable (verify with `./run_tests.sh integration`)
- MCP server running and accessible (check with `claude mcp list`)

---

## Tool Trace Capture

Every manual test session produces a trace file: a chronological JSON record of the
agent's MCP tool calls and reasoning text. Use these files to verify methodology
compliance and pass them to Claude for quality evaluation.

### One-time setup

Add to `.env`:
```
DASHBOARD_RETAIN_LOGS=1   # keep session NDJSON logs after each session
```

Then restart the watcher service:
```bash
sudo systemctl restart oncall-watcher
```

> Remove or set to `0` when done with the testing round.

### After each test session

Once the agent session completes, extract the trace (auto-finds the latest session log):
```bash
python3 testing/extract_tool_trace.py --test-id <test-id>
```

Examples:
```bash
python3 testing/extract_tool_trace.py --test-id OC-001-ospf-passive
python3 testing/extract_tool_trace.py --test-id OC-001-bgp-default-route
```

Output is written to `testing/manual_results/<test-id>_<timestamp>.json` (gitignored).

To specify a particular session file instead of auto-detecting the latest:
```bash
python3 testing/extract_tool_trace.py --test-id OC-001-ospf-passive --file logs/.session-oncall-20260316-140522.tmp
```

### Evaluation

After completing a set of manual tests, pass the trace files to Claude for evaluation.
Each trace contains the full narrative (reasoning + MCP tools + tool results in order)
which allows evaluation of:
- Methodology compliance (Principles 1–7 from CLAUDE.md)
- Correct tool sequencing (traceroute before protocol tools, one device at a time)
- Reasoning quality (correct conclusions drawn from tool results)
- Unnecessary or missing tool calls

---

## On-Call Mode Tests

These tests validate the full watcher → agent pipeline. The watcher monitors
`/var/log/network.json`, detects SLA Down events, and spawns a Claude agent session.

### Setup for all On-Call tests

In a separate terminal, start the watcher:
```bash
cd /home/mcp/aiNOC
python3 oncall/watcher.py
```

Also monitor `/var/log/network.json`:
```bash
tail -f /var/log/network.json
```

Monitor the watcher log in another terminal:
```bash
tail -f /home/mcp/aiNOC/logs/oncall_watcher.log
```

---

### OC-001 — Full On-Call Pipeline (SLA Failure → Diagnosis → Fix → Deferred Documentation)

**Tests**: Full watcher pipeline, agent investigation, fix verification, deferred documentation, Jira documentation

Run this test manually for Tier 1 regression and full pipeline validation.

---

#### OSPF Passive Interface Break (A1C)

**SLA Path**: `A1C_TO_IAN` | **Break device**: A1C | **SLA source**: A1C (172.20.20.205)
**Implicit**: A1C has a second SLA probe (SLA 2) that also fires — validates deferred documentation with concurrent failures

##### Setup (break)

First, identify A1C's OSPF interface(s) toward the core (C1C/C2C). Verify with:
```
get_ospf("A1C", "interfaces")
```
Note the interface name(s) where C1C and C2C neighbors are seen.

Push via `push_config` to A1C (adjust interface name as needed):
```
router ospf 1
  passive-interface <A1C_interface_toward_core>
```
(Making the OSPF-facing interface passive drops both Area 1 adjacencies — C1C and C2C neighbors lost.)

##### Verify break

From A1C:
```
show ip ospf neighbor
```
Expected: C1C and C2C **absent**.

From A1C:
```
show ip route 10.0.0.26
```
Expected: Route to E1C loopback `10.0.0.26` **absent** (no inter-area routes without ABR adjacency).

##### Check /var/log/network.json

Two IP SLA paths fail as a result of the misconfiguration:
```
{"device":"172.20.20.205","facility":"local7","msg":"BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down","severity":"info","ts":"2026-03-01T07:26:05.065Z"}
{"device":"172.20.20.205","facility":"local7","msg":"BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down","severity":"info","ts":"2026-03-01T07:26:09.841Z"}
```

##### Check logs/oncall_watcher.log

Agent starts working on the first failure (reported by A1C):
```
[2026-03-01 07:26:06 UTC] Agent invoked for event on A1C: BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down
```
Claude Code session opens automatically in the terminal where `oncall/watcher.py` runs.

##### Expected agent behavior

1. Reads `skills/oncall/SKILL.md`
2. Looks up `A1C_TO_IAN` in `sla_paths/paths.json` → scope: A1C, C1C, C2C, E1C, E2C, IAN
3. Traceroutes from A1C (source 10.1.1.5) to `200.40.40.2` → fails at first hop (A1C has no route)
4. Reads `skills/ospf/SKILL.md`
5. Calls `get_ospf(A1C, "neighbors")` → C1C and C2C missing
6. Calls `get_ospf(A1C, "interfaces")` → shows `passive` on the core-facing interface
7. Proposes removing passive-interface on A1C
8. Requests operator approval via Discord (posts embed with ✅/❌ reactions)
9. Applies fix, verifies A1C route to 10.0.0.26 returns
10. Documents the issue to the Jira ticket (if Jira is configured)

**NOTE: Keep the session open and see Deferred Queue steps below after verifying the fix!**

##### Verify fix

From A1C:
```
show ip ospf neighbor
```
Expected: C1C and C2C FULL.

In `/var/log/network.json`:
```
{"device":"172.20.20.205","facility":"local7","msg":"BOM%TRACK-6-STATE: 1 ip sla 1 reachability Down -> Up","severity":"info","ts":"2026-03-01T07:33:45.102Z"}
```

From A1C:
```
show ip route 10.0.0.26
show ip sla statistics
```
Expected: Route present; latest operation return code: OK.

##### Documentation check

- Jira ticket updated with findings and resolution (if Jira is configured)
- `Verification: PASSED`
- `Case Status: FIXED`

##### Teardown (if agent did not fix)

```
router ospf 1
  no passive-interface <A1C_interface_toward_core>
```

---

#### Deferred Failure Documentation

**Purpose**: Validate that concurrent SLA events during an active session are documented to Jira and Discord after the session ends.

**Reason**: The setup above breaks at least two SLA paths at once. The agent is invoked for the **first failure only**. If a second failure occurs during the investigation of the first, the watcher logs it as SKIPPED — no second agent session is spawned.

11. After the agent session completes (auto-exits in print mode), verify in `logs/oncall_watcher.log`:
```
SKIPPED (deferred - occurred during active session) - A1C (172.20.20.205): BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down
Documenting 1 deferred failure(s) to Jira/Discord
Deferred failures documented to Jira ticket <key>
Deferred failures posted to Discord
Resuming monitoring.
```
12. Verify Jira: original ticket has a new comment titled "Deferred SLA Failures" listing the concurrent events
13. Verify Discord: an orange informational embed "⚠️ Deferred SLA Failures" appears in the channel with the event list

---

---

## Watcher Behavior Validation

These checks can be done without breaking lab config.

### WB-004 — tmux Session + Session Logging ★ Primary Mode

**This is the only mode. Always verify this first.**

The watcher always runs Claude in tmux + print mode (`-p`). Claude auto-exits when done. No interactive CLI or `--service` flag.

#### A) Manual invocation (dev/testing)

Start the watcher:
```bash
python3 oncall/watcher.py
```

Inject an SLA Down event:
```bash
echo '{"ts":"2026-01-01T00:00:00Z","device":"172.20.20.205","msg":"%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down"}' | sudo tee -a /var/log/network.json
```

Verify:
1. A tmux session named `oncall-<timestamp>` is created: `tmux list-sessions | grep oncall`
2. `logs/oncall_watcher.log` shows: `Agent invoked in tmux session: oncall-<timestamp>` and `Session log: logs/session-oncall-<timestamp>.md`
3. A notification is written to all open terminals and a desktop popup appears (if `notify-send` is available)
4. Agent completes and auto-exits — **no `/exit` needed**
5. Watcher resumes monitoring: `Agent session ended.` then `Resuming monitoring.` in log, no dangling lock file
6. Session log exists and contains agent output: `cat logs/session-oncall-<timestamp>.md`
7. tmux session is **killed** after cleanup — session log preserves all output for post-incident review

#### B) Systemd service

```bash
sudo systemctl status oncall-watcher.service
```
Expected: `Active: active (running)` and `ExecStart` shows `watcher.py` (no `--service` flag).

To restart after code changes:
```bash
sudo systemctl restart oncall-watcher.service
sudo journalctl -u oncall-watcher -f
```

> **Note**: Deferred documentation is verified as part of OC-001 steps 11-13. SSH retry logic is covered by automated tests (UT-013).

---

---

## Case Documentation Checks

After any On-Call test run (Jira must be configured):

1. **Jira ticket updated with findings**:
   Check the Jira ticket (SUP project) for a comment with the full case structure from `case_format.md`.

2. **Case comment contains required fields**:
   All fields described in `cases/case_format.md` are present: Commands Used, Proposed Fixes, Verification.

3. **Lessons learned** (check if `cases/lessons.md` was updated - not always the case, the agent decides).

---

---

# OSPF & BGP Protocol Troubleshooting Test Suite

Manual scenarios for validating the agent's ability to diagnose and fix OSPF and BGP faults. The **operator** applies the break config directly on devices via SSH/console. The **agent** (Claude + MCP tools) is then invoked to diagnose and propose a fix.

## Purpose

- Cover all 7 OSPF neighbor adjacency criteria
- Cover all 6 BGP session formation criteria
- Cover all 11 BGP path selection attributes (where topology allows)
- Progress from simple (timer mismatches) to complex (policy interactions, area type issues)
- Every test is reproducible: same config change → same failure every time

## Prerequisites

1. Lab up and all devices reachable:
   ```bash
   sudo clab redeploy -t AINOC-TOPOLOGY.yml
   PYTHONPATH=/home/mcp/aiNOC /home/mcp/aiNOC/mcp/bin/pytest testing/agent-testing/unit/ -q
   ```
2. MCP server running: `claude mcp list`
3. For approval-gate tests: Discord configured or operator ready to manually approve
4. Operator SSHes into devices using management IPs from `inventory/NETWORK.json`
5. **FORBIDDEN set note**: `clear ip ospf`, `clear ip bgp`, `clear ip route`, `no router` cannot be pushed via MCP `push_config`. The operator runs these directly on devices. The agent advises the operator to run them manually.

## Topology Quick Reference

| Device | Role | Platform | Mgmt IP | Key Interfaces |
|--------|------|----------|---------|----------------|
| A1C | OSPF Area 1 leaf | IOL | 172.20.20.205 | Eth1/3→C1C, Eth1/2→C2C |
| A2C | OSPF Area 1 leaf | IOL | 172.20.20.206 | Eth1/2→C1C, Eth1/3→C2C |
| C1C | ABR (Area 0+1) | c8000v | 172.20.20.207 | Gi2→A1C, Gi3→A2C, Gi4→C2C, Gi5→E2C, Gi6→E1C |
| C2C | ABR (Area 0+1) | c8000v | 172.20.20.208 | Gi3→A1C, Gi2→A2C, Gi4→C1C, Gi6→E2C, Gi5→E1C |
| E1C | ASBR+NAT (Area 0) | c8000v | 172.20.20.209 | Gi2→C1C, Gi3→C2C, Gi5→IAN, Gi4→IBN |
| E2C | ASBR+NAT (Area 0) | c8000v | 172.20.20.210 | Gi2→C2C, Gi3→C1C, Gi4→IAN, Gi5→IBN |
| IAN | ISP-A edge | IOL | 172.20.20.220 | Eth0/1→E1C, Eth0/2→E2C, Eth0/3→X1C |
| IBN | ISP-B edge | IOL | 172.20.20.230 | Eth0/2→E1C, Eth0/1→E2C, Eth0/3→X1C |
| X1C | Remote site ASBR | c8000v | 172.20.20.240 | Gi2→IAN, Gi3→IBN |

**Key IP Ranges**: Area 1: 10.1.1.0/24 · Area 0: 10.0.0.0/24 · ISP-A: 200.40.x.x · ISP-B: 200.50.x.x

**SLA Paths**: `A1C_TO_X1C` (primary ABR: C1C) · `A2C_TO_X1C` (primary ABR: C2C) · `E1C_TO_E2C` · `C1C_TO_IBN` · `C2C_TO_IAN`

## Coverage Matrix

| Test | Criterion / Attribute | Group |
|------|-----------------------|-------|
| OSPF-001 | Hello timer mismatch | OSPF Adj Fundamentals |
| OSPF-002 | Dead timer mismatch | OSPF Adj Fundamentals |
| OSPF-003 | Area ID mismatch | OSPF Adj Fundamentals |
| OSPF-004 | Stub area type mismatch | OSPF Adj Fundamentals |
| OSPF-005 | Network type mismatch | OSPF Adj Fundamentals |
| OSPF-006 | MD5 auth one-side | OSPF Adj Fundamentals |
| OSPF-007 | Passive interface | OSPF Adj Fundamentals |
| OSPF-008 | MTU mismatch (EXSTART stuck) | OSPF Adj Fundamentals |
| OSPF-009 | Duplicate Router ID | OSPF Adj Fundamentals |
| OSPF-010 | Interface admin-down | Interface & Process State |
| OSPF-011 | IP subnet mismatch | Interface & Process State |
| OSPF-012 | Passive-interface default | Interface & Process State |
| OSPF-013 | Interface cost manipulation | Cost & Path Selection |
| OSPF-014 | Reference-bandwidth mismatch | Cost & Path Selection |
| OSPF-015 | Unequal cost breaks ECMP | Cost & Path Selection |
| OSPF-016 | Max-metric router LSA | Cost & Path Selection |
| OSPF-017 | Default-originate removed (one edge) | Route Presence & Filtering |
| OSPF-018 | Both default originators removed | Route Presence & Filtering |
| OSPF-019 | Distribute-list filtering default | Route Presence & Filtering |
| OSPF-020 | Area range not-advertise | Route Presence & Filtering |
| OSPF-021 | ACL blocking OSPF multicast | Route Presence & Filtering |
| OSPF-022 | Route summarization black hole | Route Presence & Filtering |
| OSPF-023 | Totally stubby conversion | Area Type & ABR |
| OSPF-024 | Stub-to-NSSA type mismatch | Area Type & ABR |
| OSPF-025 | ABR backbone isolation | Area Type & ABR |
| OSPF-026 | E1 vs E2 external metric type | Area Type & ABR |
| OSPF-027 | DR priority zero (no DR election) | Area Type & ABR |
| BGP-001 | Neighbor admin shutdown | BGP Session Formation |
| BGP-002 | AS number mismatch | BGP Session Formation |
| BGP-003 | Wrong neighbor IP | BGP Session Formation |
| BGP-004 | MD5 auth mismatch | BGP Session Formation |
| BGP-005 | ACL blocking TCP 179 | BGP Session Formation |
| BGP-006 | Update-source to unreachable address | BGP Session Formation |
| BGP-007 | Peering interface shutdown | BGP Session Formation |
| BGP-008 | Null route blocking peer | BGP Session Formation |
| BGP-009 | Aggressive hold timer | BGP Session Formation |
| BGP-010 | Default-originate removed | Route Advertisement & Filtering |
| BGP-011 | Outbound route-map deny all | Route Advertisement & Filtering |
| BGP-012 | Inbound prefix-list blocks default | Route Advertisement & Filtering |
| BGP-013 | Address-family deactivation | Route Advertisement & Filtering |
| BGP-014 | Outbound prefix-list filters transit | Route Advertisement & Filtering |
| BGP-015 | Next-hop set to unreachable | Route Advertisement & Filtering |
| BGP-016 | Prefix-list blocking specific prefix | Route Advertisement & Filtering |
| BGP-017 | AS-path loop prevention | Route Advertisement & Filtering |
| BGP-018 | Maximum-prefix limit exceeded | Route Advertisement & Filtering |
| BGP-019 | Weight — prefer ISP-B | Path Selection Attributes |
| BGP-020 | Local preference via route-map | Path Selection Attributes |
| BGP-021 | AS-path prepending | Path Selection Attributes |
| BGP-022 | MED manipulation | Path Selection Attributes |
| BGP-023 | Origin code change | Path Selection Attributes |
| BGP-024 | Router ID tiebreaker | Path Selection Attributes |
| BGP-025 | Weight overrides AS-path length | Path Selection Attributes |
| BGP-026 | Local preference overrides AS-path | Path Selection Attributes |
| BGP-027 | Conditional default-originate | Path Selection Attributes |
| BGP-028 | Soft reset required after policy change | Path Selection Attributes |

## Untestable Items

| Item | Reason |
|------|--------|
| BGP criterion #5: ebgp-multihop | All peers directly connected; no multi-hop path exists in this topology |
| BGP best-path #7: eBGP over iBGP | All-eBGP topology; no iBGP sessions configured |
| BGP best-path #8: IGP metric to next-hop | All eBGP peers are directly connected; IGP metric to peer is always 0 |
| BGP best-path #9: Oldest eBGP route | Timing-dependent; not reproducible across resets |
| NO_EXPORT community | No iBGP or customer/transit hierarchy; effect not observable |

---

---

## OSPF Tests

### Group 1: Adjacency Fundamentals

---

### OSPF-001: Hello Timer Mismatch

**Concept**: OSPF adjacency criterion #1 — Hello/dead timers must match on both sides of a link.
**Difficulty**: Simple
**Devices**: A1C
**SLA Impact**: A1C_TO_X1C

**Setup (Break)**

SSH to A1C (172.20.20.205):
```
configure terminal
interface Ethernet1/3
 ip ospf hello-interval 15
end
```
This sets A1C's hello interval to 15s (dead auto-adjusts to 60s). C1C stays at default 10s hello / 40s dead — mismatch.

**Verify Break**

On A1C:
```
show ip ospf neighbor
```
Expected: C1C entry (via Eth1/3) disappears within 40 seconds (C1C's dead timer expires when it stops receiving hellos at the expected rate, then A1C's mismatched hellos get dropped).

On C1C:
```
show ip ospf neighbor
```
Expected: A1C entry absent.

**Expected Symptoms**

- Agent traceroutes from A1C toward X1C — traceroute fails at first hop (no inter-area route)
- `get_ospf(A1C, "neighbors")` — C1C missing (A1C only has C2C remaining if Eth1/2 still healthy)
- `get_ospf(A1C, "interfaces")` — Eth1/3 shows hello-interval 15, dead-interval 60
- `get_ospf(C1C, "interfaces")` — Gi2 shows hello-interval 10, dead-interval 40 → mismatch confirmed

**Root Cause**

A1C Ethernet1/3 has a non-default hello interval (15s) that does not match C1C's default (10s); OSPF adjacency with C1C cannot form.

**Expected Fix**

Agent proposes via `request_approval` → `push_config` on **A1C**:
```
interface Ethernet1/3
 no ip ospf hello-interval 15
```
(Restores default 10s/40s to match C1C — fix the misconfigured side, not the correctly-configured peer.)

**Teardown**

```
configure terminal
interface Ethernet1/3
 no ip ospf hello-interval 15
end
```

---

### OSPF-002: Dead Timer Mismatch

**Concept**: OSPF adjacency criterion #1 — dead interval must match. Unlike hello-interval, dead-interval is NOT auto-derived from hello on IOS-XE when set explicitly.
**Difficulty**: Simple
**Devices**: C1C
**SLA Impact**: C1C_TO_IBN, E1C_TO_E2C, A1C_TO_X1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet6
 ip ospf dead-interval 80
end
```
C1C Gi6→E1C now advertises dead-interval 80. E1C Gi2 stays at default dead-interval 40. Mismatch → adjacency drops.

**Verify Break**

On C1C:
```
show ip ospf neighbor
```
Expected: E1C entry (via Gi6) absent within ~80 seconds.

On E1C:
```
show ip ospf neighbor
```
Expected: C1C entry (via Gi2) absent.

**Expected Symptoms**

- Traceroute from C1C to IBN (200.50.50.2) fails — C1C loses E1C as ABR exit
- `get_ospf(C1C, "neighbors")` — E1C missing
- `get_ospf(C1C, "interfaces")` — Gi6 shows dead-interval 80
- `get_ospf(E1C, "interfaces")` — Gi2 shows dead-interval 40 → mismatch confirmed

**Root Cause**

C1C GigabitEthernet6 has a manually configured dead-interval (80s) that does not match E1C's default (40s); the OSPF adjacency between C1C and E1C cannot form.

**Expected Fix**

Agent proposes on **C1C**:
```
interface GigabitEthernet6
 no ip ospf dead-interval 80
```

**Teardown**

```
configure terminal
interface GigabitEthernet6
 no ip ospf dead-interval 80
end
```

---

### OSPF-003: Area ID Mismatch

**Concept**: OSPF adjacency criterion #2 — both sides of a link must be in the same OSPF area.
**Difficulty**: Simple
**Devices**: A1C
**SLA Impact**: A1C_TO_X1C

**Setup (Break)**

SSH to A1C (172.20.20.205):
```
configure terminal
interface Ethernet1/3
 ip ospf 1 area 0
end
```
A1C Eth1/3 moves from Area 1 to Area 0. C1C Gi2 is in Area 1. Area ID mismatch → adjacency drops immediately.

**Verify Break**

On A1C:
```
show ip ospf neighbor
show ip ospf interface Ethernet1/3
```
Expected: C1C absent; Eth1/3 shows area 0.

**Expected Symptoms**

- Traceroute from A1C to X1C fails at A1C
- `get_ospf(A1C, "neighbors")` — C1C missing
- `get_ospf(A1C, "interfaces")` — Eth1/3 in Area 0
- `get_ospf(C1C, "interfaces")` — Gi2 in Area 1 → area mismatch confirmed

**Root Cause**

A1C Ethernet1/3 is configured in OSPF Area 0 but C1C GigabitEthernet2 expects Area 1 on this link; the area ID mismatch prevents adjacency.

**Expected Fix**

Agent proposes on **A1C**:
```
interface Ethernet1/3
 ip ospf 1 area 1
```

**Teardown**

```
configure terminal
interface Ethernet1/3
 ip ospf 1 area 1
end
```

---

### OSPF-004: Stub Area Type Mismatch

**Concept**: OSPF adjacency criterion #2 — area type (stub/normal) is signaled in the Hello packet's options field. Mismatched area types prevent adjacency.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: A1C_TO_X1C, A2C_TO_X1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
router ospf 1
 no area 1 stub
end
```
C1C now treats Area 1 as a normal area. A1C and A2C still send stub-bit hellos (E-bit=0). C1C sends normal hellos (E-bit=1). The options mismatch causes C1C to silently drop A1C/A2C hellos → adjacency cannot form.

**Verify Break**

On C1C:
```
show ip ospf neighbor
```
Expected: A1C and A2C absent (Gi2 and Gi3 neighbors gone).

On A1C:
```
show ip ospf neighbor
```
Expected: C1C absent (A1C still tries to form with C2C which still has stub config).

**Expected Symptoms**

- Both A1C_TO_X1C and A2C_TO_X1C fail (C1C cannot inject Type 3 LSAs into Area 1)
- `get_ospf(C1C, "neighbors")` — A1C and A2C missing
- `get_ospf(C1C, "config")` — Area 1 not configured as stub
- `get_ospf(A1C, "config")` — Area 1 configured as stub → type mismatch confirmed

**Root Cause**

C1C Area 1 is configured as a normal area (stub removed) while A1C and A2C still advertise stub-bit hellos for Area 1; the area type mismatch prevents OSPF adjacency.

**Expected Fix**

Agent proposes on **C1C** (ABR is the authoritative side for area type):
```
router ospf 1
 area 1 stub
```

**Teardown**

```
configure terminal
router ospf 1
 area 1 stub
end
```

---

### OSPF-005: Network Type Mismatch (Point-to-Point vs Broadcast)

**Concept**: OSPF adjacency criterion #3 — network type affects DR/BDR election and Hello interval. P2P and broadcast can form adjacency but with asymmetric routing consequences.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: A1C_TO_X1C (routing inconsistency)

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet2
 ip ospf network point-to-point
end
```
C1C Gi2 is now P2P; A1C Eth1/3 stays broadcast. The adjacency may still form (IOS-XE is lenient about this mismatch) but routing breaks: P2P side does not elect DR/BDR and uses different LSA origination. The subnet may be installed differently in the LSDB, causing route inconsistency or black-holes.

**Verify Break**

On C1C:
```
show ip ospf interface GigabitEthernet2
```
Expected: Network Type POINT_TO_POINT.

On A1C:
```
show ip ospf interface Ethernet1/3
```
Expected: Network Type BROADCAST.

Check routing:
```
show ip route ospf
```
Look for missing or inconsistent Area 1 subnets on C1C.

**Expected Symptoms**

- Traceroute from A1C may succeed intermittently or fail for specific destinations
- `get_ospf(C1C, "interfaces")` — Gi2 shows network type point-to-point
- `get_ospf(A1C, "interfaces")` — Eth1/3 shows network type broadcast → type mismatch detected
- Agent may observe partial route installation or asymmetric LSA entries

**Root Cause**

C1C GigabitEthernet2 is configured as point-to-point while A1C Ethernet1/3 uses the default broadcast network type; this asymmetry causes inconsistent LSDB entries and routing anomalies on the C1C–A1C link.

**Expected Fix**

Agent proposes on **C1C** (fix the misconfigured side):
```
interface GigabitEthernet2
 no ip ospf network point-to-point
```

**Teardown**

```
configure terminal
interface GigabitEthernet2
 no ip ospf network point-to-point
end
```

---

### OSPF-006: MD5 Authentication — One Side Only

**Concept**: OSPF adjacency criterion #4 — authentication must match. Enabling MD5 on one side without the other causes OSPF packets to be dropped.
**Difficulty**: Simple
**Devices**: C1C
**SLA Impact**: A1C_TO_X1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet2
 ip ospf message-digest-key 1 md5 SECRET123
 ip ospf authentication message-digest
end
```
C1C Gi2 now requires MD5 auth. A1C Eth1/3 has no auth configured → C1C drops A1C's unauthenticated hellos; adjacency drops.

**Verify Break**

On C1C:
```
show ip ospf neighbor
show ip ospf interface GigabitEthernet2
```
Expected: A1C absent; interface shows auth type MD5.

On A1C:
```
show ip ospf neighbor
```
Expected: C1C absent (A1C may log "Invalid authentication type" messages).

**Expected Symptoms**

- Traceroute from A1C to X1C fails at A1C
- `get_ospf(C1C, "neighbors")` — A1C missing
- `get_ospf(C1C, "interfaces")` — Gi2 shows authentication type MD5
- `get_ospf(A1C, "interfaces")` — Eth1/3 shows no authentication → auth mismatch confirmed

**Root Cause**

C1C GigabitEthernet2 has MD5 authentication enabled but A1C Ethernet1/3 has no authentication configured; C1C drops A1C's unauthenticated OSPF hellos.

**Expected Fix**

Agent proposes on **C1C** (authentication was added to a correctly-configured peer; remove from the misconfigured side):
```
interface GigabitEthernet2
 no ip ospf authentication message-digest
 no ip ospf message-digest-key 1 md5 SECRET123
```

**Teardown**

```
configure terminal
interface GigabitEthernet2
 no ip ospf authentication message-digest
 no ip ospf message-digest-key 1 md5 SECRET123
end
```

---

### OSPF-007: Passive Interface on Transit Link

**Concept**: OSPF adjacency criterion #5 — passive-interface suppresses OSPF hellos, preventing adjacency formation on that interface.
**Difficulty**: Simple
**Devices**: C2C
**SLA Impact**: E1C_TO_E2C, A2C_TO_X1C

**Setup (Break)**

SSH to C2C (172.20.20.208):
```
configure terminal
router ospf 1
 passive-interface GigabitEthernet6
end
```
C2C Gi6 connects to E2C. Making it passive stops hellos → E2C neighbor drops. C2C also loses the E2C→IBN path, affecting E1C_TO_E2C traceroute routing.

**Verify Break**

On C2C:
```
show ip ospf neighbor
show ip ospf interface GigabitEthernet6
```
Expected: E2C absent; Gi6 shows as PASSIVE.

On E2C:
```
show ip ospf neighbor
```
Expected: C2C absent (via Gi2 connection toward C2C, but note: C2C Gi6 connects to E2C).

**Expected Symptoms**

- Traceroute from E1C to E2C may reroute via C1C→C2C path and succeed, or fail if C2C→E2C is the only path
- `get_ospf(C2C, "neighbors")` — E2C missing
- `get_ospf(C2C, "interfaces")` — Gi6 shows PASSIVE
- Agent checks intent: C2C Gi6 should connect to E2C, not be passive

**Root Cause**

C2C GigabitEthernet6 (link to E2C) is configured as a passive OSPF interface; C2C does not send hellos on this transit link, so the C2C–E2C adjacency cannot form.

**Expected Fix**

Agent proposes on **C2C**:
```
router ospf 1
 no passive-interface GigabitEthernet6
```

**Teardown**

```
configure terminal
router ospf 1
 no passive-interface GigabitEthernet6
end
```

---

### OSPF-008: MTU Mismatch — EXSTART Stuck

**Concept**: OSPF adjacency criterion #6 — MTU mismatch causes DBD exchange failure; adjacency gets stuck in EXSTART/EXCHANGE state.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: C1C_TO_IBN, E1C_TO_E2C, A1C_TO_X1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet6
 ip mtu 1400
end
```
C1C Gi6 MTU is now 1400. E1C Gi2 stays at 1500. When DBD packets exceed 1400 bytes, C1C drops them → EXSTART state, never reaching FULL.

**Verify Break**

On C1C:
```
show ip ospf neighbor
```
Expected: E1C entry stuck in EXSTART or EXCHANGE (not FULL), or absent after dead timer.

On E1C:
```
show ip ospf neighbor
```
Expected: C1C stuck or absent.

On C1C:
```
show interface GigabitEthernet6 | include MTU
```
Expected: MTU 1400 bytes.

**Expected Symptoms**

- Traceroute from C1C toward IBN fails (no route through E1C/E2C)
- `get_interfaces(C1C)` — Gi6 shows MTU 1400
- `get_ospf(C1C, "neighbors")` — E1C stuck in EXSTART or absent
- `get_ospf(E1C, "neighbors")` — C1C same state
- Agent checks both sides: E1C Gi2 MTU 1500 vs C1C Gi6 MTU 1400 → mismatch confirmed

**Root Cause**

C1C GigabitEthernet6 has an IP MTU of 1400 bytes while E1C GigabitEthernet2 uses the default 1500 bytes; the MTU mismatch causes OSPF DBD packets to be dropped, leaving the adjacency stuck in EXSTART.

**Expected Fix**

Agent proposes on **C1C** (fix the non-default side):
```
interface GigabitEthernet6
 no ip mtu 1400
```

**Teardown**

```
configure terminal
interface GigabitEthernet6
 no ip mtu 1400
end
```

---

### OSPF-009: Duplicate Router ID

**Concept**: OSPF adjacency criterion #7 — Router IDs must be unique. Duplicate RIDs cause LSDB confusion and adjacency instability.
**Difficulty**: Medium
**Devices**: A2C
**SLA Impact**: A1C_TO_X1C, A2C_TO_X1C

**Setup (Break)**

First, check A1C's current router ID:
```
show ip ospf | include Router ID
```
Note the value (e.g., `1.1.1.1` or derived from highest loopback).

SSH to A2C (172.20.20.206):
```
configure terminal
router ospf 1
 router-id 1.1.1.1
end
clear ip ospf process
```
Type `yes` when prompted. A2C now uses A1C's Router ID. Both devices claim the same RID → LSDB oscillation, adjacency instability, route flapping.

> **Note**: `clear ip ospf process` is in the FORBIDDEN set for MCP push_config. The operator runs it manually via SSH. This is intentional — the operator applies the break, not the agent.

**Verify Break**

On C1C:
```
show ip ospf neighbor
show ip ospf database router
```
Expected: Instability — neighbor states oscillate, duplicate RID warning in syslog, route flapping observed.

**Expected Symptoms**

- Intermittent traceroute failures for A1C_TO_X1C and A2C_TO_X1C
- `get_ospf(C1C, "neighbors")` — A1C and A2C may show unstable states
- `get_ospf(C1C, "database")` — duplicate Router LSAs with same RID
- Agent checks A1C and A2C router IDs: both show same value → duplicate RID confirmed

**Root Cause**

A2C has been configured with a Router ID that duplicates A1C's Router ID; the duplicate RID causes OSPF LSDB inconsistency, route oscillation, and adjacency instability throughout Area 1.

**Expected Fix**

Agent proposes on **A2C** (restore unique router-id, then operator manually clears process):
```
router ospf 1
 router-id 2.2.2.2
```
Then agent advises operator to run manually on A2C: `clear ip ospf process` (confirm with `yes`).

**Teardown**

```
configure terminal
router ospf 1
 router-id 2.2.2.2
end
clear ip ospf process
```
(Confirm `yes`. Restores A2C's original unique router-id.)

---

### Group 2: Interface & Process State

---

### OSPF-010: Interface Admin Shutdown

**Concept**: An interface shutdown removes the connected network from OSPF, dropping the adjacency and all routes learned through that link.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: C1C_TO_IBN, A1C_TO_X1C

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
interface GigabitEthernet2
 shutdown
end
```
E1C Gi2 connects to C1C. Shutdown removes the link; OSPF adjacency with C1C drops immediately.

**Verify Break**

On E1C:
```
show interface GigabitEthernet2
show ip ospf neighbor
```
Expected: Gi2 is administratively down; C1C absent from neighbor table.

On C1C:
```
show ip ospf neighbor
```
Expected: E1C absent (via Gi6).

**Expected Symptoms**

- `get_interfaces(E1C)` — Gi2 shows admin-down
- `get_ospf(E1C, "neighbors")` — C1C missing
- Agent stops investigation at this point per Principle 3 (interface admin-down = root cause found)

**Root Cause**

E1C GigabitEthernet2 (link to C1C) is administratively shut down; the interface-down state removes the OSPF adjacency and all routes learned via this link.

**Expected Fix**

Agent proposes on **E1C**:
```
interface GigabitEthernet2
 no shutdown
```

**Teardown**

```
configure terminal
interface GigabitEthernet2
 no shutdown
end
```

---

### OSPF-011: IP Subnet Mismatch

**Concept**: If both sides of a link are in different subnets, OSPF hellos are exchanged on the wire but the router ignores hellos from a peer that is not in the same subnet (IOS default behavior for broadcast networks).
**Difficulty**: Simple
**Devices**: A1C
**SLA Impact**: A1C_TO_X1C

**Setup (Break)**

SSH to A1C (172.20.20.205):
```
configure terminal
interface Ethernet1/3
 ip address 10.1.1.1 255.255.255.252
end
```
A1C Eth1/3 was 10.1.1.5/30. Now it is 10.1.1.1/30 (different subnet from C1C's 10.1.1.6/30 which is in 10.1.1.4/30). IOS ignores OSPF hellos from a non-subnet peer → adjacency cannot form.

> **Note**: Management access to A1C is via 172.20.20.205 (out-of-band) — changing the OSPF interface IP does not affect lab connectivity.

**Verify Break**

On A1C:
```
show ip ospf neighbor
show ip interface Ethernet1/3
```
Expected: C1C absent; interface shows 10.1.1.1/30.

On C1C:
```
show ip ospf neighbor
```
Expected: A1C absent (C1C receives A1C's hellos but source IP 10.1.1.1 is not in the 10.1.1.4/30 subnet → discarded).

**Expected Symptoms**

- Traceroute from A1C to X1C fails
- `get_interfaces(A1C)` — Eth1/3 shows IP 10.1.1.1/30 (intent says 10.1.1.5/30)
- `get_ospf(A1C, "neighbors")` — C1C missing
- Agent compares actual IP against INTENT.json → subnet mismatch detected

**Root Cause**

A1C Ethernet1/3 has an incorrect IP address (10.1.1.1/30) that places it in a different subnet than C1C GigabitEthernet2 (10.1.1.6/30 in 10.1.1.4/30); OSPF ignores hellos from out-of-subnet peers.

**Expected Fix**

Agent proposes on **A1C**:
```
interface Ethernet1/3
 ip address 10.1.1.5 255.255.255.252
```

**Teardown**

```
configure terminal
interface Ethernet1/3
 ip address 10.1.1.5 255.255.255.252
end
```

---

### OSPF-012: Passive-Interface Default

**Concept**: `passive-interface default` makes ALL interfaces passive process-wide, suppressing hellos on every interface including transit links.
**Difficulty**: Medium
**Devices**: C2C
**SLA Impact**: E1C_TO_E2C, A2C_TO_X1C, C2C_TO_IAN

**Setup (Break)**

SSH to C2C (172.20.20.208):
```
configure terminal
router ospf 1
 passive-interface default
end
```
All C2C OSPF interfaces become passive — C2C drops adjacencies with A1C, A2C, C1C, E1C, and E2C simultaneously.

**Verify Break**

On C2C:
```
show ip ospf neighbor
show ip ospf interface
```
Expected: No neighbors; all interfaces show PASSIVE.

**Expected Symptoms**

- Multiple SLA paths fail simultaneously
- `get_ospf(C2C, "neighbors")` — all neighbors missing (A1C, A2C, C1C, E2C gone)
- `get_ospf(C2C, "config")` — passive-interface default present
- Agent recognizes total neighbor loss indicates process-level config, not per-link issue

**Root Cause**

C2C has `passive-interface default` configured under `router ospf 1`; this makes all interfaces passive process-wide, suppressing OSPF hellos on all transit links and dropping all adjacencies.

**Expected Fix**

Agent proposes on **C2C**:
```
router ospf 1
 no passive-interface default
```

**Teardown**

```
configure terminal
router ospf 1
 no passive-interface default
end
```

---

### Group 3: Cost & Path Selection

---

### OSPF-013: Interface Cost Manipulation

**Concept**: Increasing an interface cost shifts traffic to lower-cost alternate paths. Tests the agent's ability to detect asymmetric cost config and correlate with path changes.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: C1C_TO_IBN (path change)

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet6
 ip ospf cost 10000
end
```
C1C Gi6 (to E1C) now has cost 10000. Traffic from C1C destined for IBN prefers C1C→E2C (via C1C Gi5 to E2C) or reroutes via C2C rather than through E1C.

**Verify Break**

On C1C:
```
show ip route 200.50.50.2
show ip ospf interface GigabitEthernet6
```
Expected: Route to IBN no longer uses next-hop 10.0.0.26 (E1C); Gi6 shows cost 10000.

**Expected Symptoms**

- Traceroute from C1C to IBN takes unexpected path (via E2C or C2C→E2C)
- `get_ospf(C1C, "interfaces")` — Gi6 shows cost 10000 vs default 1
- `get_routing(C1C, prefix="0.0.0.0/0")` — next-hop changes from E1C to E2C or via C2C
- Agent identifies the non-default cost as the cause of the path change

**Root Cause**

C1C GigabitEthernet6 has a manually configured OSPF cost of 10000 (vs default 1), causing OSPF to prefer alternate paths to external destinations via E2C rather than E1C.

**Expected Fix**

Agent proposes on **C1C**:
```
interface GigabitEthernet6
 no ip ospf cost 10000
```

**Teardown**

```
configure terminal
interface GigabitEthernet6
 no ip ospf cost 10000
end
```

---

### OSPF-014: Reference Bandwidth Mismatch

**Concept**: `auto-cost reference-bandwidth` changes how interface costs are calculated. A mismatch between routers causes asymmetric costs, creating routing loops or suboptimal paths.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: Path selection changes throughout Area 0

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router ospf 1
 auto-cost reference-bandwidth 10000
end
```
E1C now calculates all interface costs using 10000 Mbps reference (GigE = cost 10). All other devices use default 100 Mbps (GigE = cost 1). E1C's LSAs advertise costs 10x higher → routes via E1C become expensive from other routers' perspectives, but E1C itself sees low-cost paths to peers.

**Verify Break**

On E1C:
```
show ip ospf interface GigabitEthernet2
```
Expected: Cost 10 (was 1 with default reference bandwidth).

On C1C:
```
show ip route ospf
```
Check if routes that should traverse E1C are now going via E2C due to cost discrepancy.

**Expected Symptoms**

- Path selection shifts — E1C-sourced routes may be preferred or avoided inconsistently
- `get_ospf(E1C, "interfaces")` — shows cost 10 on GigE links
- `get_ospf(C1C, "interfaces")` — shows cost 1 on GigE links → reference-bandwidth mismatch
- Agent checks E1C config: `auto-cost reference-bandwidth 10000` present, other devices at default

**Root Cause**

E1C has `auto-cost reference-bandwidth 10000` configured, resulting in OSPF costs 10x higher than all other devices using the default reference bandwidth (100 Mbps); this asymmetry causes inconsistent path selection across the area.

**Expected Fix**

Agent proposes on **E1C**:
```
router ospf 1
 no auto-cost reference-bandwidth 10000
```

**Teardown**

```
configure terminal
router ospf 1
 no auto-cost reference-bandwidth 10000
end
```

---

### OSPF-015: Unequal Cost Breaks ECMP

**Concept**: OSPF ECMP requires equal-cost paths. Artificially inflating one path's cost removes it from the equal-cost set.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: E1C_TO_E2C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet5
 ip ospf cost 500
end
```
C1C Gi5 connects to E2C. Cost 500 makes the C1C→E2C path more expensive than C1C→E1C (cost 1). Any traffic transiting C1C toward E2C destinations now takes a suboptimal or absent path.

**Verify Break**

On C1C:
```
show ip route 10.0.0.36
show ip ospf interface GigabitEthernet5
```
Expected: Route to E2C-C2C subnet (10.0.0.36/30) uses Gi6→E1C as next hop; Gi5 shows cost 500.

**Expected Symptoms**

- Traceroute from E1C to E2C may still work but via longer path (E1C→C1C→C2C→E2C or similar)
- `get_ospf(C1C, "interfaces")` — Gi5 shows cost 500 vs Gi6 cost 1
- `get_routing(C1C)` — routes to E2C subnets use E1C as next-hop instead of direct Gi5
- Agent identifies the asymmetric cost causing ECMP loss

**Root Cause**

C1C GigabitEthernet5 (link to E2C) has a manually configured OSPF cost of 500, removing it from the equal-cost path set and causing traffic to E2C to be rerouted via E1C.

**Expected Fix**

Agent proposes on **C1C**:
```
interface GigabitEthernet5
 no ip ospf cost 500
```

**Teardown**

```
configure terminal
interface GigabitEthernet5
 no ip ospf cost 500
end
```

---

### OSPF-016: Max-Metric Router LSA (Traffic Drain)

**Concept**: `max-metric router-lsa` causes a router to advertise all its links with maximum metric (0xFFFF), making it the last resort for transit traffic. Used for graceful maintenance but catastrophic if left configured.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: All paths transiting C1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
router ospf 1
 max-metric router-lsa
end
```
C1C advertises all internal link costs as 65535. SPF on all other devices calculates routes around C1C. Transit traffic drains away from C1C.

**Verify Break**

On A1C:
```
show ip route ospf
```
Expected: Routes to Area 0 and external prefixes prefer C2C as ABR (lower metric path) instead of C1C.

On C1C:
```
show ip ospf database router self-originate
```
Expected: All link costs show 65535.

**Expected Symptoms**

- Traceroute from A1C to X1C transits C2C instead of C1C (or C1C is avoided entirely)
- `get_ospf(C1C, "config")` — `max-metric router-lsa` present
- `get_ospf(C1C, "database")` — C1C's own router LSA shows max metric
- Agent recognizes max-metric as maintenance mode config left in production

**Root Cause**

C1C has `max-metric router-lsa` configured, causing it to advertise all link costs at the maximum value (65535) and drain all transit traffic away from itself; this is a maintenance-drain command that was not removed after maintenance.

**Expected Fix**

Agent proposes on **C1C**:
```
router ospf 1
 no max-metric router-lsa
```

**Teardown**

```
configure terminal
router ospf 1
 no max-metric router-lsa
end
```

---

### Group 4: Route Presence & Filtering

---

### OSPF-017: Default Route Originate Removed (One Edge)

**Concept**: `default-information originate always` injects a Type 5 external LSA for 0.0.0.0/0 into OSPF. Removing it from one edge router reduces the default route's redundancy.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: Partial — E1C-sourced default lost; E2C still provides default

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router ospf 1
 no default-information originate always
end
```
E1C stops injecting the default route into OSPF. E2C still originates its own default. Area 0 and Area 1 devices still receive a default, but only from E2C. If E2C is also the best-path, this may not be visible until E2C fails.

**Verify Break**

On C1C:
```
show ip route 0.0.0.0
show ip ospf database external
```
Expected: Only one Type 5 LSA for 0.0.0.0/0 (from E2C, not E1C); or E1C's LSA absent.

**Expected Symptoms**

- SLA paths may still work (E2C provides default)
- `get_ospf(E1C, "config")` — `default-information originate` absent
- `get_ospf(C1C, "database")` — only one external LSA for 0.0.0.0/0 (from E2C's RID)
- Agent identifies reduced redundancy: one ASBR no longer originating default

**Root Cause**

E1C no longer has `default-information originate always` configured; it is not injecting a default route into OSPF, leaving E2C as the sole default route originator and eliminating path redundancy.

**Expected Fix**

Agent proposes on **E1C**:
```
router ospf 1
 default-information originate always metric-type 1
```

**Teardown**

```
configure terminal
router ospf 1
 default-information originate always metric-type 1
end
```

---

### OSPF-018: Both Default Originators Removed (Full Default Loss)

**Concept**: Removing `default-information originate always` from both E1C and E2C leaves the entire OSPF domain with no default route — all internet-bound traffic fails.
**Difficulty**: Complex
**Devices**: E1C + E2C

**SLA Impact**: A1C_TO_X1C, A2C_TO_X1C

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router ospf 1
 no default-information originate always
end
```

SSH to E2C (172.20.20.210):
```
configure terminal
router ospf 1
 no default-information originate always
end
```
No Type 5 LSA for 0.0.0.0/0 exists anywhere. All OSPF routers lose their default route.

**Verify Break**

On A1C:
```
show ip route 0.0.0.0
```
Expected: No default route entry (0.0.0.0/0 absent).

On C1C:
```
show ip ospf database external
```
Expected: No external LSAs for 0.0.0.0/0.

**Expected Symptoms**

- Traceroute from A1C to X1C (200.40.8.1) fails — no default route on A1C
- `get_ospf(C1C, "database")` — no external LSAs for 0.0.0.0/0
- `get_ospf(E1C, "config")` — default-information originate absent
- `get_ospf(E2C, "config")` — default-information originate absent
- Agent identifies both ASBRs not originating default

**Root Cause**

Neither E1C nor E2C has `default-information originate always` configured; no default route LSA exists in the OSPF domain, so all routers lack a default route for external destinations.

**Expected Fix**

Agent proposes on **E1C** and **E2C** (separate push_config calls, same commands):
```
router ospf 1
 default-information originate always metric-type 1
```

**Teardown**

On both E1C and E2C:
```
configure terminal
router ospf 1
 default-information originate always metric-type 1
end
```

---

### OSPF-019: Distribute-List Filtering Default Route from RIB

**Concept**: A distribute-list filters routes from the RIB without removing LSAs from the LSDB. The agent must distinguish between "LSDB has the LSA but route not in RIB" vs "LSA absent entirely".
**Difficulty**: Complex
**Devices**: C1C
**SLA Impact**: C1C_TO_IBN

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
router ospf 1
 distribute-list prefix BLOCK-DEFAULT in
end
```
C1C has the Type 5 LSA for 0.0.0.0/0 in its LSDB (from E1C/E2C), but the distribute-list prevents the route from being installed in the RIB. C1C cannot forward to external destinations.

**Verify Break**

On C1C:
```
show ip route 0.0.0.0
```
Expected: No entry (route absent from RIB despite LSA in LSDB).

```
show ip ospf database external
```
Expected: External LSA for 0.0.0.0/0 still present (LSA in LSDB but not in RIB).

**Expected Symptoms**

- Traceroute from C1C to IBN (200.50.50.2) fails (no default route on C1C)
- `get_routing(C1C)` — no default route
- `get_ospf(C1C, "database")` — external LSA for 0.0.0.0/0 present → LSA exists but route not in RIB
- `get_ospf(C1C, "config")` or `get_routing_policies(C1C)` — distribute-list with BLOCK-DEFAULT found
- Agent distinguishes LSDB-present vs RIB-absent → distribute-list filter identified

**Root Cause**

C1C has a distribute-list (`prefix BLOCK-DEFAULT`) applied inbound under `router ospf 1` that filters the 0.0.0.0/0 default route from being installed in the RIB; the LSA exists in the LSDB but the route is absent from the routing table.

**Expected Fix**

Agent proposes on **C1C**:
```
router ospf 1
 no distribute-list prefix BLOCK-DEFAULT in
```

**Teardown**

```
configure terminal
router ospf 1
 no distribute-list prefix BLOCK-DEFAULT in
no ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
no ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
end
```

---

### OSPF-020: Area Range with not-advertise (Route Suppression)

**Concept**: `area X range Y not-advertise` on an ABR suppresses the summary Type 3 LSA for the covered range from being advertised into the backbone. Area 1 subnets become unreachable from Area 0.
**Difficulty**: Complex
**Devices**: C1C
**SLA Impact**: A1C_TO_X1C, A2C_TO_X1C (return path affected)

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
router ospf 1
 area 1 range 10.1.1.0 255.255.255.0 not-advertise
end
```
C1C suppresses all Area 1 subnets (10.1.1.0/24 range) from being summarized into Area 0. E1C, E2C, and X1C no longer have routes back to A1C and A2C. Return traffic fails.

**Verify Break**

On E1C:
```
show ip route 10.1.1.0
```
Expected: No route to 10.1.1.0/24 or any /30 within it.

On C1C:
```
show ip ospf database summary
```
Expected: No Type 3 LSA for 10.1.1.0/24.

**Expected Symptoms**

- Traceroute from A1C to X1C: A1C can send packets (has OSPF-learned route via C2C ABR) but X1C's return path fails
- `get_ospf(C1C, "config")` — `area 1 range 10.1.1.0 255.255.255.0 not-advertise` present
- `get_ospf(E1C, "database")` — no Type 3 LSA for Area 1 subnets from C1C
- Agent traces the missing return path to C1C's area range suppression

**Root Cause**

C1C has `area 1 range 10.1.1.0 255.255.255.0 not-advertise` configured, suppressing all Area 1 subnet advertisements into the backbone; external routers (E1C, E2C, X1C) have no return path to Area 1 devices.

**Expected Fix**

Agent proposes on **C1C**:
```
router ospf 1
 no area 1 range 10.1.1.0 255.255.255.0 not-advertise
```

**Teardown**

```
configure terminal
router ospf 1
 no area 1 range 10.1.1.0 255.255.255.0 not-advertise
end
```

---

### OSPF-021: ACL Blocking OSPF Multicast

**Concept**: An inbound ACL blocking 224.0.0.5/224.0.0.6 (OSPF multicast addresses) on a transit interface silently drops OSPF hellos and updates, causing the adjacency to drop.
**Difficulty**: Medium
**Devices**: C1C
**SLA Impact**: C1C_TO_IBN, A1C_TO_X1C

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
ip access-list extended BLOCK-OSPF
 deny ip any host 224.0.0.5
 deny ip any host 224.0.0.6
 permit ip any any
exit
interface GigabitEthernet6
 ip access-group BLOCK-OSPF in
end
```
Inbound ACL on Gi6 blocks OSPF Hello and LSU multicast packets from E1C → C1C drops the adjacency.

**Verify Break**

On C1C:
```
show ip ospf neighbor
show ip access-lists BLOCK-OSPF
```
Expected: E1C absent; ACL shows hit counters incrementing for the deny rules.

**Expected Symptoms**

- Traceroute from C1C to IBN fails (no E1C neighbor)
- `get_interfaces(C1C)` — Gi6 shows access-group BLOCK-OSPF in
- `get_ospf(C1C, "neighbors")` — E1C missing
- `get_routing_policies(C1C)` — BLOCK-OSPF ACL found with deny rules for OSPF multicast
- Agent identifies ACL as the cause (not a protocol misconfiguration)

**Root Cause**

An extended ACL (BLOCK-OSPF) applied inbound on C1C GigabitEthernet6 is dropping OSPF multicast packets (224.0.0.5 and 224.0.0.6) from E1C, preventing C1C from receiving E1C's OSPF hellos and updates.

**Expected Fix**

Agent proposes on **C1C**:
```
interface GigabitEthernet6
 no ip access-group BLOCK-OSPF in
```
(Optionally also remove the ACL itself: `no ip access-list extended BLOCK-OSPF`)

**Teardown**

```
configure terminal
interface GigabitEthernet6
 no ip access-group BLOCK-OSPF in
no ip access-list extended BLOCK-OSPF
end
```

---

### OSPF-022: Route Summarization Black Hole

**Concept**: `area X range` without `not-advertise` creates a summary LSA in Area 0 and installs a Null0 route on the ABR. Traffic to subnets not actually present in Area 1 (but within the summary range) is black-holed at the ABR.
**Difficulty**: Complex
**Devices**: C1C
**SLA Impact**: Design awareness — traffic to non-existent subnets in range is silently dropped

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
router ospf 1
 area 1 range 10.1.0.0 255.255.0.0
end
```
C1C advertises a 10.1.0.0/16 summary into Area 0. C1C also installs a Null0 route for 10.1.0.0/16. Traffic destined to any 10.1.x.x address not covered by a specific /30 subnet (e.g., 10.1.5.1) is black-holed at C1C via Null0.

**Verify Break**

On C1C:
```
show ip route 10.1.0.0
```
Expected: `O N1 10.1.0.0/16 is directly connected, Null0` — Null0 summary route installed.

On E1C:
```
show ip route 10.1.0.0
```
Expected: Only the /16 summary (no specific /30s visible in Area 0).

**Expected Symptoms**

- Pings to 10.1.5.1 (non-existent) are black-holed at C1C (Null0 route matches the /16)
- `get_ospf(C1C, "config")` — `area 1 range 10.1.0.0 255.255.0.0` present
- `get_routing(C1C, prefix="10.1.0.0/16")` — Null0 next-hop visible
- Agent identifies the overly broad summary range causing a black-hole for non-existent subnets

**Root Cause**

C1C has a broad area range (10.1.0.0/16) configured for Area 1, causing it to advertise a /16 summary and install a Null0 route; traffic destined to any 10.1.x.x address outside the actual /30 subnets is silently dropped.

**Expected Fix**

Agent proposes on **C1C** (remove or tighten the range):
```
router ospf 1
 no area 1 range 10.1.0.0 255.255.0.0
```

**Teardown**

```
configure terminal
router ospf 1
 no area 1 range 10.1.0.0 255.255.0.0
end
```

---

### Group 5: Area Type & ABR Issues

---

### OSPF-023: Totally Stubby Conversion

**Concept**: Converting a stub area to totally stubby suppresses all Type 3 inter-area LSAs from the ABR. Area 1 devices only receive a default route — all specific inter-area routes disappear.
**Difficulty**: Complex
**Devices**: C1C + C2C
**SLA Impact**: Functional with default route; specific prefix reachability lost for Area 1

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
router ospf 1
 area 1 stub no-summary
end
```

SSH to C2C (172.20.20.208):
```
configure terminal
router ospf 1
 area 1 stub no-summary
end
```
Both ABRs now suppress all Type 3 LSAs into Area 1. A1C and A2C only see a Type 3 default route (0.0.0.0/0) — no specific Area 0 or external routes.

**Verify Break**

On A1C:
```
show ip route ospf
```
Expected: Only `O*IA 0.0.0.0/0` present; all specific 10.0.0.x inter-area routes absent.

**Expected Symptoms**

- Traceroute from A1C to X1C works IF X1C accepts the default-forwarded packet through the path
- `get_ospf(A1C, "database")` — only default route Type 3 LSA; no specific inter-area summaries
- `get_ospf(C1C, "config")` — `area 1 stub no-summary` present
- Agent identifies totally stubby as the source of missing inter-area routes

**Root Cause**

Both C1C and C2C have `area 1 stub no-summary` configured, converting Area 1 to totally stubby; the ABRs suppress all Type 3 LSAs into Area 1, leaving Area 1 devices with only a default route and no specific inter-area prefixes.

**Expected Fix**

Agent proposes on **C1C** and **C2C** (separate push_config calls):
```
router ospf 1
 area 1 stub
```
(Changes from totally stubby back to regular stub — Type 3 LSAs are restored.)

**Teardown**

On both C1C and C2C:
```
configure terminal
router ospf 1
 area 1 stub
end
```

---

### OSPF-024: Stub-to-NSSA Area Type Mismatch

**Concept**: If one ABR changes Area 1 from stub to NSSA while the other ABR and all Area 1 devices still expect stub, the N-bit vs E-bit mismatch in Hello options causes adjacencies to drop between the NSSA-configured ABR and Area 1 devices.
**Difficulty**: Complex
**Devices**: C2C
**SLA Impact**: A2C_TO_X1C

**Setup (Break)**

SSH to C2C (172.20.20.208):
```
configure terminal
router ospf 1
 no area 1 stub
 area 1 nssa
end
```
C2C now sends N-bit hellos for Area 1. A1C and A2C still send E-bit=0 (stub) hellos. The options mismatch causes C2C to reject hellos from A1C and A2C → C2C loses its Area 1 adjacencies.

**Verify Break**

On C2C:
```
show ip ospf neighbor
show ip ospf interface GigabitEthernet3
```
Expected: A1C and A2C absent from C2C's neighbor table; interface shows area type NSSA.

On A2C:
```
show ip ospf neighbor
```
Expected: C2C absent (A2C still has C1C as neighbor since C1C still has `area 1 stub`).

**Expected Symptoms**

- A2C_TO_X1C fails (A2C loses C2C as ABR; only C1C remains)
- `get_ospf(C2C, "neighbors")` — A1C and A2C missing
- `get_ospf(C2C, "config")` — area 1 is NSSA
- `get_ospf(C1C, "config")` — area 1 is stub → area type mismatch between ABRs confirmed
- Agent checks A1C/A2C config: still stub → three-way mismatch

**Root Cause**

C2C has Area 1 configured as NSSA while C1C, A1C, and A2C still have it as stub; the OSPF Hello options bit mismatch (N-bit vs E-bit) prevents C2C from forming adjacencies with Area 1 devices.

**Expected Fix**

Agent proposes on **C2C** (revert to stub to match the rest of Area 1):
```
router ospf 1
 no area 1 nssa
 area 1 stub
```

**Teardown**

```
configure terminal
router ospf 1
 no area 1 nssa
 area 1 stub
end
```

---

### OSPF-025: ABR Backbone Isolation

**Concept**: An ABR must have at least one active Area 0 interface to maintain ABR status. Shutting down all Area 0 interfaces on C1C removes its ABR status — it can no longer inject Type 3 LSAs between Area 0 and Area 1.
**Difficulty**: Complex
**Devices**: C1C
**SLA Impact**: A1C_TO_X1C (primary ABR gone; C2C is fallback)

**Setup (Break)**

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet4
 shutdown
interface GigabitEthernet5
 shutdown
interface GigabitEthernet6
 shutdown
end
```
Gi4=C2C, Gi5=E2C, Gi6=E1C — all Area 0 interfaces on C1C are now down. C1C loses ABR status. Area 1 routes are no longer injected by C1C. A1C/A2C still have C2C as working ABR.

**Verify Break**

On C1C:
```
show ip ospf
```
Expected: C1C no longer shows as ABR (no `Area 0` in active interface list).

On A1C:
```
show ip route ospf
```
Expected: Routes still present (via C2C as fallback ABR), but only one path available.

```
show ip ospf neighbor
```
Expected: C1C still present (Area 1 interfaces Gi2/Gi3 still up) but C1C's ABR-originated Type 3 LSAs disappear from the LSDB.

**Expected Symptoms**

- A1C_TO_X1C may still work (via C2C) or fail if C2C also has issues
- `get_ospf(C1C, "neighbors")` — C2C, E1C, E2C all absent (backbone interfaces down)
- `get_interfaces(C1C)` — Gi4, Gi5, Gi6 all admin-down
- Agent identifies multiple backbone interfaces shut, ABR status lost

**Root Cause**

C1C GigabitEthernet4, Gi5, and Gi6 (all Area 0 interfaces) are administratively shut down; C1C has lost its ABR status and can no longer exchange routes between Area 0 and Area 1.

**Expected Fix**

Agent proposes on **C1C**:
```
interface GigabitEthernet4
 no shutdown
interface GigabitEthernet5
 no shutdown
interface GigabitEthernet6
 no shutdown
```

**Teardown**

```
configure terminal
interface GigabitEthernet4
 no shutdown
interface GigabitEthernet5
 no shutdown
interface GigabitEthernet6
 no shutdown
end
```

---

### OSPF-026: E1 vs E2 External Metric Type

**Concept**: Type E1 externals add the internal OSPF cost to the external metric; Type E2 externals use only the external metric. When E1C uses E2 and E2C uses E1 (or vice versa), the path preference changes because E2 metrics do not accumulate internal cost.
**Difficulty**: Complex
**Devices**: E1C
**SLA Impact**: Path selection — traffic shifts to prefer E2C's default

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router ospf 1
 default-information originate always metric-type 2
end
```
E1C's default route LSA changes from E1 to E2. E2C still uses E1 (the default per intent). For any router farther from E2C (paying more internal cost), E2C's E1 route accumulates more internal cost and may lose to E1C's E2 or win — depending on topology distances. At equal internal distances, E1 is preferred over E2 at the same metric.

**Verify Break**

On C1C:
```
show ip route 0.0.0.0
```
Check which ASBR is preferred (should shift from E1C to E2C if E1C's metric type changed to E2 while E2C stays E1).

On A1C:
```
show ip ospf database external
```
Expected: E1C's external LSA shows metric type E2; E2C's shows E1.

**Expected Symptoms**

- Traceroute from A1C to X1C may switch to prefer E2C path
- `get_ospf(E1C, "config")` — `default-information originate always metric-type 2`
- `get_ospf(E2C, "config")` — `default-information originate always metric-type 1` (default)
- Agent identifies the E1/E2 mismatch between the two ASBRs and explains the path shift

**Root Cause**

E1C has `default-information originate always metric-type 2` configured while E2C uses the default metric-type 1 (E1); E1 routes are always preferred over E2 routes at equal metric, causing E2C's default to be preferred over E1C's.

**Expected Fix**

Agent proposes on **E1C** (restore consistent metric type):
```
router ospf 1
 default-information originate always metric-type 1
```

**Teardown**

```
configure terminal
router ospf 1
 default-information originate always metric-type 1
end
```

---

### OSPF-027: DR Priority Zero (No DR Election)

**Concept**: Setting `ip ospf priority 0` on all routers on a broadcast segment prevents any DR/BDR election. Without a DR, adjacency on broadcast networks stays in 2-WAY state — no routes are exchanged via that segment.
**Difficulty**: Complex
**Devices**: A1C + C1C
**SLA Impact**: A1C_TO_X1C

**Setup (Break)**

SSH to A1C (172.20.20.205):
```
configure terminal
interface Ethernet1/3
 ip ospf priority 0
end
clear ip ospf process
```
Confirm `yes`.

SSH to C1C (172.20.20.207):
```
configure terminal
interface GigabitEthernet2
 ip ospf priority 0
end
clear ip ospf process
```
Confirm `yes`.

> **Note**: DR election is non-preemptive (RFC 2328 §9.4). Changing priority alone does not remove an existing DR — the OSPF process must be restarted to force a new election. `clear ip ospf process` is in the FORBIDDEN set for MCP push_config; the operator runs it manually.

With both sides at priority 0, no DR or BDR is elected. The adjacency stays in 2-WAY state. No LSAs are flooded via this segment → A1C loses routes learned through C1C.

**Verify Break**

On A1C:
```
show ip ospf neighbor
```
Expected: C1C shows state 2WAY/DROTHER (not FULL).

On C1C:
```
show ip ospf neighbor
```
Expected: A1C shows state 2WAY/DROTHER.

**Expected Symptoms**

- A1C has no inter-area routes (or routes only via C2C which still has a working DR)
- `get_ospf(A1C, "neighbors")` — C1C shows 2WAY not FULL
- `get_ospf(A1C, "interfaces")` — Eth1/3 shows priority 0, no DR elected
- `get_ospf(C1C, "interfaces")` — Gi2 shows priority 0, no DR → both sides at priority 0 confirmed

**Root Cause**

Both A1C Ethernet1/3 and C1C GigabitEthernet2 have OSPF priority set to 0, preventing DR/BDR election on this broadcast segment; without a DR, the adjacency remains in 2-WAY state and no routing information is exchanged.

**Expected Fix**

Agent proposes on **A1C** (restore default priority on the leaf side; C1C's default priority 1 will win DR election):
```
interface Ethernet1/3
 no ip ospf priority 0
```
Then advises operator to run manually on A1C: `clear ip ospf process` (confirm `yes`).

**Teardown**

On A1C:
```
configure terminal
interface Ethernet1/3
 no ip ospf priority 0
end
clear ip ospf process
```

On C1C:
```
configure terminal
interface GigabitEthernet2
 no ip ospf priority 0
end
clear ip ospf process
```

---

---

## BGP Tests

### Group 1: Session Formation

---

### BGP-001: Neighbor Admin Shutdown

**Concept**: `neighbor X shutdown` places a BGP session in Idle/Admin state. The session does not attempt to reconnect until the shutdown is removed.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 neighbor 200.40.40.2 shutdown
end
```

**Verify Break**

On E1C:
```
show ip bgp summary
```
Expected: IAN neighbor (200.40.40.2) shows state `Idle (Admin)`.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 in Idle Admin state
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — shows `Administratively shut down`
- Agent identifies admin shutdown as root cause immediately

**Root Cause**

E1C has `neighbor 200.40.40.2 shutdown` configured; the BGP session to IAN (AS4040) is administratively disabled.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 shutdown
```

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 shutdown
end
```

---

### BGP-002: AS Number Mismatch

**Concept**: BGP session formation criterion #1 — the remote-as value must match the peer's actual AS number. If they differ, the OPEN message is rejected with a NOTIFICATION.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 remote-as 4040
 neighbor 200.40.40.2 remote-as 4041
end
```
> **Note**: `no neighbor X remote-as Y` removes the entire neighbor statement and all sub-configuration. Capture E1C's full neighbor config for 200.40.40.2 before applying this break so teardown is accurate.

E1C expects IAN to be AS4041. IAN is actually AS4040 → OPEN rejected, NOTIFICATION sent → session stays in Active/Idle.

**Verify Break**

On E1C:
```
show ip bgp summary
```
Expected: 200.40.40.2 shows state Active (repeatedly trying to connect but OPEN rejected).

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 stuck in Active
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — remote-as 4041 shown
- `get_bgp(IAN, "summary")` — E1C entry shows NOTIFICATION or Active (IAN receives OPEN with wrong AS)
- Agent cross-checks INTENT.json: IAN is AS4040, E1C configured with 4041 → mismatch

**Root Cause**

E1C has `neighbor 200.40.40.2 remote-as 4041` configured but IAN is AS4040; the AS number mismatch causes the BGP OPEN to be rejected with a NOTIFICATION error.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 remote-as 4041
 neighbor 200.40.40.2 remote-as 4040
```
> Agent should also restore any removed sub-config (route-maps, timers, etc.) — see teardown.

**Teardown**

Restore the full original neighbor config on E1C (capture before breaking):
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 remote-as 4041
 neighbor 200.40.40.2 remote-as 4040
end
```

---

### BGP-003: Wrong Neighbor IP

**Concept**: BGP session formation criterion #3 — the configured neighbor IP must be reachable. A wrong neighbor IP causes TCP SYN to a non-existent host → session stays in Active.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 remote-as 4040
 neighbor 200.40.40.3 remote-as 4040
end
```
> **Note**: Same warning as BGP-002 — `no neighbor X remote-as` removes all sub-config. Capture full neighbor config before breaking.

E1C now tries to TCP-connect to 200.40.40.3 (non-existent). TCP SYN times out → session stays Active.

**Verify Break**

On E1C:
```
show ip bgp summary
```
Expected: 200.40.40.3 shows Active (and 200.40.40.2 no longer listed).

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.3 stuck in Active; 200.40.40.2 absent
- Agent compares configured neighbor IP against INTENT.json: IAN peer should be 200.40.40.2
- Ping to 200.40.40.3 fails (no ARP response) → unreachable IP confirmed

**Root Cause**

E1C has BGP neighbor configured to 200.40.40.3 (non-existent IP) instead of IAN's actual address 200.40.40.2; TCP connection attempts time out and the session cannot reach Established.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.3 remote-as 4040
 neighbor 200.40.40.2 remote-as 4040
```

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.3 remote-as 4040
 neighbor 200.40.40.2 remote-as 4040
end
```

---

### BGP-004: MD5 Authentication Mismatch

**Concept**: BGP session formation criterion #6 — MD5 passwords must match on both sides. IOS sends an MD5-signed TCP segment; if the peer doesn't have MD5 configured (or uses a different key), the TCP segment is dropped.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 neighbor 200.40.40.2 password WRONG123
end
```
IAN has no MD5 configured. E1C signs TCP segments with MD5; IAN's TCP stack rejects them (no matching key) → TCP session never establishes.

**Verify Break**

On E1C:
```
show ip bgp summary
```
Expected: 200.40.40.2 stuck in Active (TCP RST from IAN or no response).

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 in Active
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — password configured (MD5 enabled)
- `get_bgp(IAN, "neighbors", neighbor="200.40.40.1")` — no password configured → mismatch
- Agent identifies MD5 auth on one side only

**Root Cause**

E1C has MD5 authentication configured for neighbor 200.40.40.2 (password WRONG123) but IAN has no MD5 configured; the TCP MD5 signature mismatch prevents the BGP TCP session from establishing.

**Expected Fix**

Agent proposes on **E1C** (remove the mismatched password):
```
router bgp 1010
 no neighbor 200.40.40.2 password WRONG123
```

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 password WRONG123
end
```

---

### BGP-005: ACL Blocking TCP Port 179

**Concept**: BGP uses TCP port 179. An inbound ACL blocking TCP/179 on the BGP peering interface prevents the session from establishing.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
ip access-list extended BLOCK-BGP
 deny tcp any any eq 179
 deny tcp any eq 179 any
 permit ip any any
exit
interface GigabitEthernet5
 ip access-group BLOCK-BGP in
end
```
Blocks both incoming TCP/179 connections (IAN initiating) and replies to E1C's own SYN.

**Verify Break**

On E1C:
```
show ip bgp summary
show ip access-lists BLOCK-BGP
```
Expected: IAN neighbor (200.40.40.2) stuck in Active; ACL shows hit counters on deny rules.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 in Active
- `get_interfaces(E1C)` — Gi5 shows ip access-group BLOCK-BGP in
- `get_routing_policies(E1C)` — BLOCK-BGP ACL found with TCP/179 deny rules
- Agent identifies the ACL as the barrier (not a BGP config issue)

**Root Cause**

An extended ACL (BLOCK-BGP) applied inbound on E1C GigabitEthernet5 (link to IAN) is blocking TCP port 179 traffic, preventing the BGP TCP session from establishing.

**Expected Fix**

Agent proposes on **E1C**:
```
interface GigabitEthernet5
 no ip access-group BLOCK-BGP in
```

**Teardown**

```
configure terminal
interface GigabitEthernet5
 no ip access-group BLOCK-BGP in
no ip access-list extended BLOCK-BGP
end
```

---

### BGP-006: Update-Source Set to Unreachable Loopback

**Concept**: BGP session formation criterion #4 — the update-source must be reachable by the peer. Setting update-source to a loopback with no route to it on the peer side causes TCP to fail.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
interface Loopback99
 ip address 192.168.99.1 255.255.255.255
exit
router bgp 1010
 neighbor 200.40.40.2 update-source Loopback99
end
```
E1C sources BGP TCP from 192.168.99.1. IAN cannot route to 192.168.99.1 (no route in the routing table) → TCP SYN reply fails → session never establishes.

**Verify Break**

On E1C:
```
show ip bgp summary
show ip bgp neighbors 200.40.40.2 | include Local host
```
Expected: 200.40.40.2 in Active; local host shows 192.168.99.1.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 in Active
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — update-source Loopback99 shown
- `get_interfaces(E1C)` — Loopback99 exists with 192.168.99.1
- Agent verifies 192.168.99.1 is not in IAN's routing table → unreachable source

**Root Cause**

E1C has `neighbor 200.40.40.2 update-source Loopback99` configured, causing BGP TCP sessions to originate from 192.168.99.1; this address is not reachable from IAN so TCP replies never arrive.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 update-source Loopback99
```
(Optionally also: `no interface Loopback99`)

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 update-source Loopback99
no interface Loopback99
end
```

---

### BGP-007: Peering Interface Shutdown

**Concept**: If the physical interface carrying the BGP peering link is shut down, the peer becomes unreachable and the BGP session drops. Simplest reachability failure.
**Difficulty**: Simple
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
interface GigabitEthernet5
 shutdown
end
```
Gi5 is E1C's link to IAN (200.40.40.0/30). Physical link down → TCP session drops → BGP session drops.

**Verify Break**

On E1C:
```
show interface GigabitEthernet5
show ip bgp summary
```
Expected: Gi5 admin-down; IAN (200.40.40.2) shows Active or Idle.

**Expected Symptoms**

- `get_interfaces(E1C)` — Gi5 admin-down
- `get_bgp(E1C, "summary")` — 200.40.40.2 Active or Idle
- Agent stops at interface level per Principle 3 (admin-down = root cause)

**Root Cause**

E1C GigabitEthernet5 (link to IAN) is administratively shut down; the physical link is down and the BGP TCP session cannot be established.

**Expected Fix**

Agent proposes on **E1C**:
```
interface GigabitEthernet5
 no shutdown
```

**Teardown**

```
configure terminal
interface GigabitEthernet5
 no shutdown
end
```

---

### BGP-008: Null Route Blocking Peer Reachability

**Concept**: A static /32 Null0 route for the peer IP is more specific than the connected /30, routing BGP TCP packets to Null0 → session drops. This simulates a security blackhole mistakenly applied to a BGP peer.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
ip route 200.40.40.2 255.255.255.255 Null0
end
```
The /32 static route is more specific than the connected 200.40.40.0/30 → all packets to 200.40.40.2 are dropped. BGP TCP session terminates.

**Verify Break**

On E1C:
```
show ip route 200.40.40.2
show ip bgp summary
```
Expected: Route to 200.40.40.2 shows `S 200.40.40.2/32 is directly connected, Null0`; BGP session Active/Idle.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 Active/Idle
- `get_routing(E1C, prefix="200.40.40.2/32")` — Null0 route present
- Agent identifies the static blackhole route as blocking peer reachability
- Ping from E1C to 200.40.40.2 fails (Null0)

**Root Cause**

A static /32 Null0 route for 200.40.40.2 is installed on E1C, which is more specific than the connected /30 subnet; all packets to the IAN BGP peer are dropped by the Null0 route.

**Expected Fix**

Agent proposes on **E1C**:
```
no ip route 200.40.40.2 255.255.255.255 Null0
```

**Teardown**

```
configure terminal
no ip route 200.40.40.2 255.255.255.255 Null0
end
```

---

### BGP-009: Aggressive Hold Timer (Session Instability)

**Concept**: BGP session formation criterion #2 — hold timer is negotiated to the lower of the two peers' values. Aggressive timers (3s keepalive / 9s hold) make sessions highly susceptible to CPU hiccups and packet loss.
**Difficulty**: Medium
**Devices**: E1C + IAN
**SLA Impact**: Intermittent — A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 neighbor 200.40.40.2 timers 3 9
end
```

SSH to IAN (172.20.20.220):
```
configure terminal
router bgp 4040
 neighbor 200.40.40.1 timers 3 9
end
```
Both sides use 3s keepalive / 9s hold. Session may stay up but is fragile — any scheduling delay or packet drop causes a hold timer expiry.

**Verify Break**

On E1C:
```
show ip bgp neighbors 200.40.40.2 | include hold|keepalive
```
Expected: Hold time 9 seconds, keepalive 3 seconds.

Monitor for session flaps:
```
show ip bgp summary
```
Watch the Up/Down counter reset periodically.

**Expected Symptoms**

- BGP session may be Established but flaps intermittently
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — hold-time 9, keepalive 3 (non-standard)
- Agent flags the aggressive timers as a risk factor even if session is currently up
- INTENT.json does not specify custom timers → deviation from baseline

**Root Cause**

E1C and IAN both have aggressive BGP timers configured (keepalive 3s, hold 9s); these non-default timers make the session highly susceptible to flapping under any scheduling or packet loss event.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 timers 3 9
```
And advises operator to also run on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 timers 3 9
```

**Teardown**

On E1C:
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 timers 3 9
end
```
On IAN:
```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 timers 3 9
end
```

---

### Group 2: Route Advertisement & Filtering

---

### BGP-010: Default-Originate Removed

**Concept**: If IAN stops sending the default route via `neighbor X default-originate`, E1C loses the IAN-sourced default. This tests single-ISP default loss with E2C (via IBN) as fallback.
**Difficulty**: Medium
**Devices**: IAN
**SLA Impact**: Partial — E1C loses IAN default; IBN (E1C-IBN and E2C-IBN) still provide default

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 default-originate
end
```
> **Note**: If IAN uses `network 0.0.0.0` instead of `default-originate`, adapt the command accordingly. Verify IAN's actual config first: `show ip bgp neighbors 200.40.40.1 | include default-originate`.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
show ip route 0.0.0.0
```
Expected: Default route from IAN (next-hop 200.40.40.2) absent; only IBN-sourced default (200.50.50.2) remains.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — IAN session still Established (session up, no routes)
- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — only one default (from IBN)
- `get_bgp(IAN, "config")` — `no neighbor 200.40.40.1 default-originate` (or absent)
- Agent identifies IAN not sending default despite established session

**Root Cause**

IAN no longer has `neighbor 200.40.40.1 default-originate` configured; E1C receives no default route from IAN (AS4040), relying solely on IBN (AS5050) for the default.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 neighbor 200.40.40.1 default-originate
```

**Teardown**

```
configure terminal
router bgp 4040
 neighbor 200.40.40.1 default-originate
end
```

---

### BGP-011: Outbound Route-Map Deny All

**Concept**: An outbound deny-all route-map blocks all BGP routes from being sent to a neighbor. Combined with removing `default-originate` (which bypasses outbound route-maps), no routes reach E1C from IAN.
**Difficulty**: Medium
**Devices**: IAN
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map DENY-ALL deny 10
exit
router bgp 4040
 no neighbor 200.40.40.1 default-originate
 neighbor 200.40.40.1 route-map DENY-ALL out
end
clear ip bgp 200.40.40.1 soft out
```
> **Critical**: `default-originate` bypasses outbound route-maps entirely. Both steps are required: remove `default-originate` AND apply the deny-all route-map. Without removing default-originate, the default route still gets through despite the route-map.

**Verify Break**

On E1C:
```
show ip bgp summary
show ip bgp 0.0.0.0
```
Expected: IAN session Established but 0 prefixes received (0/0 in the Rcv/Used columns); no default from IAN.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 Established but 0 prefixes
- `get_bgp(IAN, "routing_policies")` — DENY-ALL route-map applied outbound to 200.40.40.1
- Session is up ("Established but zero prefixes" symptom)
- Agent distinguishes session-up-with-no-prefixes from session-down

**Root Cause**

IAN has a deny-all outbound route-map (DENY-ALL) applied to neighbor 200.40.40.1 and `default-originate` removed; no routes including the default are advertised to E1C despite the session being Established.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map DENY-ALL out
 neighbor 200.40.40.1 default-originate
```
Operator runs: `clear ip bgp 200.40.40.1 soft out` on IAN (FORBIDDEN in MCP — advise manually).

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map DENY-ALL out
 neighbor 200.40.40.1 default-originate
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-012: Inbound Prefix-List Blocking Default Route

**Concept**: An inbound prefix-list on E1C that denies 0.0.0.0/0 prevents the default route from being accepted from IAN — the session stays up but the default route is filtered on receipt.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (partial — IAN default filtered; IBN default still accepted)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
router bgp 1010
 neighbor 200.40.40.2 prefix-list BLOCK-DEFAULT in
end
clear ip bgp 200.40.40.2 soft in
```
> Operator runs `clear ip bgp 200.40.40.2 soft in` manually (FORBIDDEN in MCP). This activates the inbound policy for existing prefixes.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
show ip route 0.0.0.0
```
Expected: IAN default (next-hop 200.40.40.2) absent from BGP table and routing table. IBN default (200.50.50.2) still present.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — IAN session Established but reduced prefix count
- `get_routing_policies(E1C)` — BLOCK-DEFAULT prefix-list applied inbound to 200.40.40.2
- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — only IBN path present
- Agent identifies inbound policy filtering the default

**Root Cause**

E1C has an inbound prefix-list (BLOCK-DEFAULT) applied to neighbor 200.40.40.2 that denies 0.0.0.0/0; the default route from IAN is filtered at ingress and not installed in E1C's BGP table.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 prefix-list BLOCK-DEFAULT in
```
Operator runs: `clear ip bgp 200.40.40.2 soft in` on E1C (advise manually).

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 prefix-list BLOCK-DEFAULT in
no ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
no ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
end
clear ip bgp 200.40.40.2 soft in
```

---

### BGP-013: Address-Family Deactivation

**Concept**: `no neighbor X activate` in address-family ipv4 unicast removes the neighbor from the IPv4 address family. The BGP session (TCP) may stay Established but zero prefixes are exchanged.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 address-family ipv4 unicast
  no neighbor 200.40.40.2 activate
 exit-address-family
end
```
> **Note**: This behavior depends on whether address-family ipv4 was explicitly configured on E1C. If it was not, IOS uses the default address-family. Verify with `show ip bgp neighbors 200.40.40.2 | include IPv4 Unicast`.

**Verify Break**

On E1C:
```
show ip bgp summary
show ip bgp neighbors 200.40.40.2 | include IPv4
```
Expected: Session Established but IPv4 Unicast shows "not activated" or 0 prefixes.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 Established with 0 prefixes
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — IPv4 Unicast not activated
- Session is up but no routes received — "Established but zero prefixes" symptom
- Agent distinguishes address-family deactivation from outbound filtering

**Root Cause**

E1C has `no neighbor 200.40.40.2 activate` in the IPv4 unicast address-family; the session is Established but no IPv4 prefixes are exchanged with IAN.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 address-family ipv4 unicast
  neighbor 200.40.40.2 activate
 exit-address-family
```

**Teardown**

```
configure terminal
router bgp 1010
 address-family ipv4 unicast
  neighbor 200.40.40.2 activate
 exit-address-family
end
```

---

### BGP-014: Outbound Prefix-List Filtering Transit Routes

**Concept**: IAN applies an outbound prefix-list that only permits 0.0.0.0/0. E1C receives only the default route from IAN and loses all transit/specific prefixes (e.g., X1C's subnets).
**Difficulty**: Complex
**Devices**: IAN
**SLA Impact**: A1C_TO_X1C via IAN path (specific prefixes lost)

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
ip prefix-list ONLY-DEFAULT seq 5 permit 0.0.0.0/0
route-map TO-E1C-FILTER permit 10
 match ip address prefix-list ONLY-DEFAULT
exit
router bgp 4040
 neighbor 200.40.40.1 route-map TO-E1C-FILTER out
end
clear ip bgp 200.40.40.1 soft out
```
> Operator runs soft reset manually. Verify IAN has transit routes to advertise before testing: `show ip bgp | include 200.40.8`.

**Verify Break**

On E1C:
```
show ip bgp
```
Expected: Only 0.0.0.0/0 received from IAN; X1C transit prefixes (200.40.8.0/30) absent.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="200.40.8.0/30")` — route absent or only via IBN
- `get_bgp(IAN, "routing_policies")` — TO-E1C-FILTER route-map applied outbound to 200.40.40.1
- Session Established, default present, but specific prefixes filtered
- Agent identifies the outbound route-map as filtering transit routes

**Root Cause**

IAN has an outbound route-map (TO-E1C-FILTER) applied to neighbor 200.40.40.1 that only permits 0.0.0.0/0; all other BGP prefixes including X1C transit routes are filtered before being sent to E1C.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map TO-E1C-FILTER out
```
Operator runs: `clear ip bgp 200.40.40.1 soft out` on IAN (advise manually).

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map TO-E1C-FILTER out
no route-map TO-E1C-FILTER permit 10
no ip prefix-list ONLY-DEFAULT seq 5 permit 0.0.0.0/0
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-015: BGP Next-Hop Set to Unreachable Address

**Concept**: An inbound route-map on E1C sets the next-hop for IAN-received routes to an unreachable address. The routes appear in BGP table but are not installed in the RIB (next-hop not reachable).
**Difficulty**: Complex
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path — routes in BGP table but not in RIB)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
route-map BAD-NH permit 10
 set ip next-hop 172.16.99.99
exit
router bgp 1010
 neighbor 200.40.40.2 route-map BAD-NH in
end
clear ip bgp 200.40.40.2 soft in
```
Operator runs soft reset manually. All routes from IAN now have next-hop 172.16.99.99, which is not in E1C's routing table → routes are "valid" in BGP table but not active (next-hop not reachable) and not installed in RIB.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Route present in BGP table with next-hop 172.16.99.99, status `r` (RIB failure) — not `>` (best).

```
show ip route 0.0.0.0
```
Expected: Default route from IAN absent.

**Expected Symptoms**

- BGP shows route but not as best (no `>` flag); RIB does not have the route
- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — next-hop 172.16.99.99 (unreachable)
- `get_routing_policies(E1C)` — BAD-NH route-map applied inbound to 200.40.40.2
- Agent identifies "route in BGP table but not in RIB" → next-hop reachability failure

**Root Cause**

E1C has an inbound route-map (BAD-NH) that sets the next-hop for all IAN routes to 172.16.99.99 (unreachable); the routes appear in the BGP table but are not installed in the RIB because the next-hop is not reachable.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 route-map BAD-NH in
```
Operator runs: `clear ip bgp 200.40.40.2 soft in` on E1C (advise manually).

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 route-map BAD-NH in
no route-map BAD-NH permit 10
end
clear ip bgp 200.40.40.2 soft in
```

---

### BGP-016: Prefix-List Blocking Specific Prefix

**Concept**: An inbound prefix-list on E1C blocks a specific transit prefix (X1C's peering subnet). The default route is still accepted; only the targeted prefix is filtered.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C via IAN (X1C-specific prefix filtered)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
ip prefix-list BLOCK-X1C seq 5 deny 200.40.8.0/30
ip prefix-list BLOCK-X1C seq 10 permit 0.0.0.0/0 le 32
router bgp 1010
 neighbor 200.40.40.2 prefix-list BLOCK-X1C in
end
clear ip bgp 200.40.40.2 soft in
```
> Verify IAN actually advertises 200.40.8.0/30 to E1C before testing. If IAN only sends the default, adjust to a prefix IAN does advertise.

Operator runs soft reset manually.

**Verify Break**

On E1C:
```
show ip bgp 200.40.8.0
```
Expected: 200.40.8.0/30 absent from E1C's BGP table for IAN path. Default (0.0.0.0/0) still present.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="200.40.8.0/30")` — route absent from IAN path
- `get_routing_policies(E1C)` — BLOCK-X1C prefix-list applied inbound to 200.40.40.2
- Default route still works; only specific prefix is missing
- Agent identifies surgical prefix filtering

**Root Cause**

E1C has an inbound prefix-list (BLOCK-X1C) applied to neighbor 200.40.40.2 that specifically denies 200.40.8.0/30 (X1C's IAN-facing subnet); this prefix is not installed in E1C's BGP table via the IAN path.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 prefix-list BLOCK-X1C in
```
Operator runs: `clear ip bgp 200.40.40.2 soft in` on E1C.

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 prefix-list BLOCK-X1C in
no ip prefix-list BLOCK-X1C seq 5 deny 200.40.8.0/30
no ip prefix-list BLOCK-X1C seq 10 permit 0.0.0.0/0 le 32
end
clear ip bgp 200.40.40.2 soft in
```

---

### BGP-017: AS-Path Loop Prevention (Own AS in Received Path)

**Concept**: BGP loop prevention discards routes where the receiving router's own AS appears in the AS-path. IAN prepends AS1010 (E1C's own AS) into advertised routes → E1C silently discards them.
**Difficulty**: Complex
**Devices**: IAN
**SLA Impact**: A1C_TO_X1C (E1C→IAN path — all IAN routes rejected)

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map PREPEND-CUSTOMER-AS permit 10
 set as-path prepend 1010
exit
router bgp 4040
 no neighbor 200.40.40.1 default-originate
 neighbor 200.40.40.1 route-map PREPEND-CUSTOMER-AS out
end
clear ip bgp 200.40.40.1 soft out
```
> **Critical**: Must also remove `default-originate` — it bypasses outbound route-maps and would still send a default without the prepend. For the AS-loop test to work, the default must travel through the route-map (i.e., be in IAN's BGP table via `network 0.0.0.0`). Verify IAN has a network 0.0.0.0 statement or a matching BGP route.

Operator runs soft reset manually.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: No route from IAN (200.40.40.2 path absent); E1C silently drops routes with 1010 in the AS-path.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — IAN session Established but 0 prefixes (routes discarded)
- `get_bgp(IAN, "routing_policies")` — PREPEND-CUSTOMER-AS route-map adds AS1010 to outbound paths
- E1C receives the routes but discards them (own AS in path) — no log entry, silent drop
- Agent identifies as-path loop prevention: IAN advertises routes with AS1010 prepended

**Root Cause**

IAN has an outbound route-map (PREPEND-CUSTOMER-AS) that prepends AS1010 into all routes sent to E1C; E1C's BGP loop prevention discards any routes containing its own AS (1010) in the AS-path.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-CUSTOMER-AS out
 neighbor 200.40.40.1 default-originate
```
Operator runs: `clear ip bgp 200.40.40.1 soft out` on IAN.

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-CUSTOMER-AS out
 neighbor 200.40.40.1 default-originate
no route-map PREPEND-CUSTOMER-AS permit 10
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-018: Maximum-Prefix Limit Exceeded

**Concept**: `neighbor X maximum-prefix N` tears down the BGP session with a NOTIFICATION (cease/maximum-prefix) if the peer sends more than N prefixes. Session goes to Idle and must be manually cleared.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: A1C_TO_X1C (E1C→IAN path)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 neighbor 200.40.40.2 maximum-prefix 1
end
```
> **Note**: This only triggers if IAN sends more than 1 prefix. If IAN only sends the default, increase to `maximum-prefix 1` (1 prefix allowed) and verify IAN advertises exactly 1 prefix — if IAN sends 2+, the session tears down. If IAN sends only 1, try `maximum-prefix 0` or ensure IAN advertises additional routes before testing.

Immediately after applying, if IAN advertises 2+ prefixes:

**Verify Break**

On E1C:
```
show ip bgp summary
```
Expected: IAN (200.40.40.2) in Idle state, with a notification message about maximum-prefix exceeded.

```
show ip bgp neighbors 200.40.40.2 | include Maximum|prefix
```
Expected: Shows maximum-prefix limit hit and session tear-down notification.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — 200.40.40.2 Idle (not Active)
- `get_bgp(E1C, "neighbors", neighbor="200.40.40.2")` — maximum-prefix limit configured, exceeded
- Session is Idle (not Active) — distinguishes from reachability failure
- Agent identifies maximum-prefix as the cause of forced session tear-down

**Root Cause**

E1C has `neighbor 200.40.40.2 maximum-prefix 1` configured; IAN advertised more than 1 prefix, triggering the limit and causing E1C to send a NOTIFICATION cease message and tear down the session.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 maximum-prefix 1
```
Then operator runs: `clear ip bgp 200.40.40.2` on E1C to re-establish the session.

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 maximum-prefix 1
end
clear ip bgp 200.40.40.2
```

---

### Group 3: Path Selection Attributes

---

### BGP-019: Weight — Prefer ISP-B

**Concept**: BGP path selection attribute #1 — Weight is Cisco-proprietary, local to the router, and evaluated first. Higher weight wins. Setting weight 200 on IBN routes makes E1C prefer IBN for all destinations.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: Path selection — traffic shifts from IAN to IBN

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
route-map WEIGHT-IBN permit 10
 set weight 200
exit
router bgp 1010
 neighbor 200.50.50.2 route-map WEIGHT-IBN in
end
clear ip bgp 200.50.50.2 soft in
```
Operator runs soft reset manually. IBN routes get weight 200; IAN routes keep default weight 0. E1C prefers IBN for all destinations.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path (`>`) is via 200.50.50.2 (IBN), not 200.40.40.2 (IAN). Weight column shows 200 for IBN path.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — best path is IBN (weight 200 > 0)
- `get_routing_policies(E1C)` — WEIGHT-IBN route-map on neighbor 200.50.50.2 inbound
- Traceroute from A1C to X1C exits via IBN (E1C Gi4→IBN path)
- Agent identifies weight as the path selection mechanism

**Root Cause**

E1C has an inbound route-map (WEIGHT-IBN) that sets weight 200 on all routes received from IBN (200.50.50.2); since weight is evaluated first in BGP path selection, IBN paths are preferred over IAN paths for all destinations.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.50.50.2 route-map WEIGHT-IBN in
```
Operator runs: `clear ip bgp 200.50.50.2 soft in` on E1C.

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.50.50.2 route-map WEIGHT-IBN in
no route-map WEIGHT-IBN permit 10
end
clear ip bgp 200.50.50.2 soft in
```

---

### BGP-020: Local Preference via Inbound Route-Map

**Concept**: BGP path selection attribute #2 — Local Preference is shared within an AS (or between eBGP peers using inbound route-maps). Higher local preference wins. Setting LP 200 on IAN routes makes them preferred over IBN's default LP 100.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: Path selection — IAN preferred over IBN

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
route-map PREFER-IAN permit 10
 set local-preference 200
exit
router bgp 1010
 neighbor 200.40.40.2 route-map PREFER-IAN in
end
clear ip bgp 200.40.40.2 soft in
```
Operator runs soft reset manually. IAN routes get LP 200; IBN stays at default 100. E1C and any iBGP peers prefer IAN (all-eBGP topology here, so LP only affects E1C's own selection).

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path is via 200.40.40.2 (IAN) with local-pref 200 vs 100 for IBN.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — best path IAN, LP 200
- `get_routing_policies(E1C)` — PREFER-IAN route-map on 200.40.40.2 inbound
- Traceroute from A1C exits via IAN (demonstrating LP control)
- Agent identifies local-preference as the path selection mechanism

**Root Cause**

E1C has an inbound route-map (PREFER-IAN) that sets local-preference 200 on all routes from IAN; since local preference (#2 in path selection) is higher than IBN's default (100), IAN is preferred for all destinations.

**Expected Fix**

Agent proposes on **E1C**:
```
router bgp 1010
 no neighbor 200.40.40.2 route-map PREFER-IAN in
```
Operator runs: `clear ip bgp 200.40.40.2 soft in` on E1C.

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 route-map PREFER-IAN in
no route-map PREFER-IAN permit 10
end
clear ip bgp 200.40.40.2 soft in
```

---

### BGP-021: AS-Path Prepending

**Concept**: BGP path selection attribute #4 — shorter AS-path is preferred. Prepending IAN's own AS multiple times makes IAN-advertised routes less attractive, shifting traffic to IBN.
**Difficulty**: Medium
**Devices**: IAN
**SLA Impact**: Path selection — E1C shifts from IAN to IBN

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map PREPEND-OUT permit 10
 set as-path prepend 4040 4040 4040
exit
router bgp 4040
 neighbor 200.40.40.1 route-map PREPEND-OUT out
end
clear ip bgp 200.40.40.1 soft out
```
Operator runs soft reset manually. IAN routes now have AS-path `4040 4040 4040 4040` (original 4040 + 3 prepends). IBN routes have `5050`. Shorter IBN path preferred.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path via IBN (AS-path `5050`, length 1); IAN path (length 4) not best.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — best path IBN, IAN path has longer AS-path
- `get_bgp(IAN, "routing_policies")` — PREPEND-OUT route-map applied outbound to 200.40.40.1
- E1C's show bgp shows IAN path as valid but not best (longer AS-path)
- Agent identifies AS-path prepending as the cause of path shift

**Root Cause**

IAN has an outbound route-map (PREPEND-OUT) that prepends AS4040 three extra times for routes sent to E1C; the resulting AS-path length (4) is longer than IBN's path (1), making IBN the preferred exit.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-OUT out
```
Operator runs: `clear ip bgp 200.40.40.1 soft out` on IAN.

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-OUT out
no route-map PREPEND-OUT permit 10
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-022: MED Manipulation

**Concept**: BGP path selection attribute #6 — MED (Multi-Exit Discriminator) is compared between paths from the same AS (or across ASes with `bgp always-compare-med`). Lower MED is preferred. Setting MED 500 on IAN routes makes E2C path (default MED 0) preferred.
**Difficulty**: Complex
**Devices**: IAN + E1C
**SLA Impact**: Path selection — E1C prefers IBN/E2C over IAN

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map SET-MED permit 10
 set metric 500
exit
router bgp 4040
 neighbor 200.40.40.1 route-map SET-MED out
end
clear ip bgp 200.40.40.1 soft out
```

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 bgp always-compare-med
end
clear ip bgp * soft in
```
Operator runs soft resets manually. With `always-compare-med`, E1C compares MED across different ASes. IAN MED=500 vs IBN MED=0 (default) → IBN preferred.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path via IBN (MED 0); IAN path shows MED 500.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — best path IBN, IAN shows MED 500
- `get_bgp(IAN, "routing_policies")` — SET-MED route-map outbound to E1C
- `get_bgp(E1C, "config")` — `bgp always-compare-med` enabled
- Agent identifies MED as path selection mechanism and `always-compare-med` as enabling cross-AS comparison

**Root Cause**

IAN sets MED 500 on routes advertised to E1C via an outbound route-map; E1C has `bgp always-compare-med` enabled, which enables cross-AS MED comparison — IAN's MED 500 loses to IBN's default MED 0.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map SET-MED out
```
And on **E1C** (optional, restores default behavior):
```
router bgp 1010
 no bgp always-compare-med
```
Operator runs soft resets on both.

**Teardown**

On IAN:
```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map SET-MED out
no route-map SET-MED permit 10
end
clear ip bgp 200.40.40.1 soft out
```
On E1C:
```
configure terminal
router bgp 1010
 no bgp always-compare-med
end
clear ip bgp * soft in
```

---

### BGP-023: Origin Code Change

**Concept**: BGP path selection attribute #5 — Origin codes in preference order: IGP (i) > EGP (e) > Incomplete (?). Setting IAN routes to origin incomplete makes IBN's IGP-origin routes preferred.
**Difficulty**: Complex
**Devices**: IAN
**SLA Impact**: Path selection — IBN preferred over IAN

> **Pre-check**: Before running this test, verify that weight, local-preference, and AS-path length are equal for both IAN and IBN paths on E1C. If any higher-priority attribute differs, origin won't be the tiebreaker.

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map SET-INCOMPLETE permit 10
 set origin incomplete
exit
router bgp 4040
 neighbor 200.40.40.1 route-map SET-INCOMPLETE out
end
clear ip bgp 200.40.40.1 soft out
```
Operator runs soft reset manually. IAN routes arrive at E1C with origin `?` (incomplete). IBN routes have origin `i` (IGP). E1C prefers IBN.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path via IBN (origin `i`); IAN path shows `?`.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IAN path shows origin incomplete (`?`)
- `get_bgp(IAN, "routing_policies")` — SET-INCOMPLETE route-map applied outbound
- IBN path has origin `i` → IBN preferred at attribute #5 (Origin)
- Agent identifies origin code as the path selection differentiator

**Root Cause**

IAN has an outbound route-map (SET-INCOMPLETE) that changes the origin of all advertised routes to incomplete (`?`); since IGP origin (`i`) is preferred over incomplete, E1C selects IBN as the best path for all destinations.

**Expected Fix**

Agent proposes on **IAN**:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map SET-INCOMPLETE out
```
Operator runs: `clear ip bgp 200.40.40.1 soft out` on IAN.

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map SET-INCOMPLETE out
no route-map SET-INCOMPLETE permit 10
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-024: Router ID Tiebreaker

**Concept**: BGP path selection attribute #10 — when all other attributes are equal, the path from the neighbor with the lowest BGP Router ID is preferred. `bgp bestpath compare-routerid` skips the non-deterministic "oldest route" (#9) check and goes directly to RID comparison.
**Difficulty**: Complex
**Devices**: E1C + IAN
**SLA Impact**: Path selection — last resort tiebreaker

> **Setup**: This test requires all higher-priority attributes (weight, LP, local origin, AS-path, origin, MED, eBGP>iBGP, IGP metric) to be equal for both IAN and IBN paths. Start with a clean lab and verify equal attributes first.

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
router bgp 1010
 bgp bestpath compare-routerid
end
```

First, note which ISP is currently preferred (run `show ip bgp 0.0.0.0`). Then verify IAN's BGP Router ID:
```
show ip bgp neighbors 200.40.40.2 | include BGP neighbor|BGP version
```
Or on IAN:
```
show ip bgp | include Local router-id
```

To trigger the tiebreaker change, increase IAN's BGP Router ID to a higher value than IBN's:

SSH to IAN (172.20.20.220):
```
configure terminal
router bgp 4040
 bgp router-id 200.200.200.200
end
```
> **Note**: Changing `bgp router-id` resets IAN's BGP sessions. IAN's new RID (200.200.200.200) is higher than IBN's default RID (derived from highest interface). E1C prefers the neighbor with lower RID → IBN becomes preferred.

**Verify Break**

On E1C (after IAN's sessions re-establish):
```
show ip bgp 0.0.0.0
```
Expected: Best path via IBN (lower RID); IAN path present but not best.

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IBN best path, IAN path valid
- `get_bgp(E1C, "config")` — `bgp bestpath compare-routerid` enabled
- `get_bgp(IAN, "config")` — router-id 200.200.200.200
- Agent identifies RID comparison as the tiebreaker and explains attribute #10

**Root Cause**

IAN's BGP router-id was changed to 200.200.200.200 (higher value); with `bgp bestpath compare-routerid` enabled on E1C, the lower-RID neighbor (IBN) is preferred when all other attributes are equal.

**Expected Fix**

Agent proposes on **IAN** (restore original RID):
```
router bgp 4040
 no bgp router-id 200.200.200.200
```
And on **E1C** (optional, remove deterministic RID comparison):
```
router bgp 1010
 no bgp bestpath compare-routerid
```

**Teardown**

On IAN:
```
configure terminal
router bgp 4040
 no bgp router-id 200.200.200.200
end
```
On E1C:
```
configure terminal
router bgp 1010
 no bgp bestpath compare-routerid
end
```

---

### BGP-025: Weight Overrides AS-Path Length

**Concept**: Attribute priority demonstration — Weight (#1) overrides AS-path length (#4). Even if IAN has a much longer AS-path, weight 200 on IAN routes makes E1C still prefer IAN.
**Difficulty**: Complex
**Devices**: E1C + IAN
**SLA Impact**: Path selection — proves attribute priority order

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map PREPEND-OUT permit 10
 set as-path prepend 4040 4040 4040
exit
router bgp 4040
 neighbor 200.40.40.1 route-map PREPEND-OUT out
end
clear ip bgp 200.40.40.1 soft out
```

SSH to E1C (172.20.20.209):
```
configure terminal
route-map WEIGHT-IAN permit 10
 set weight 200
exit
router bgp 1010
 neighbor 200.40.40.2 route-map WEIGHT-IAN in
end
clear ip bgp 200.40.40.2 soft in
```
Operator runs soft resets manually.

IAN's AS-path is 4 hops (3 prepends + original). IBN's AS-path is 1 hop. But IAN routes have weight 200 vs IBN weight 0. Weight wins → E1C still prefers IAN despite longer path.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: Best path via IAN (weight 200) despite IAN having longer AS-path (4 hops vs IBN's 1 hop).

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IAN best (weight 200), IBN not best (weight 0)
- IAN path shows long AS-path but is still selected due to weight
- `get_routing_policies(E1C)` — WEIGHT-IAN on IAN neighbor; `get_bgp(IAN, "routing_policies")` — PREPEND-OUT applied
- Agent demonstrates: Weight (#1) evaluated before AS-path (#4) — IAN wins

**Root Cause**

(Intentional test scenario — no actual fault.) E1C has weight 200 set on IAN routes via a route-map, which takes precedence over IAN's longer AS-path; this demonstrates that Weight is evaluated before AS-path length in BGP path selection.

**Expected Fix** (teardown only — no real fault)

Remove both configurations:
```
router bgp 1010
 no neighbor 200.40.40.2 route-map WEIGHT-IAN in
```
On IAN:
```
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-OUT out
```

**Teardown**

On E1C:
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 route-map WEIGHT-IAN in
no route-map WEIGHT-IAN permit 10
end
clear ip bgp 200.40.40.2 soft in
```
On IAN:
```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-OUT out
no route-map PREPEND-OUT permit 10
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-026: Local Preference Overrides AS-Path Length

**Concept**: Same priority-order proof as BGP-025, but with Local Preference (#2) vs AS-path (#4). LP 200 on IAN routes means E1C still prefers IAN even when IAN's AS-path is 3x longer than IBN's.
**Difficulty**: Complex
**Devices**: E1C + IAN
**SLA Impact**: Path selection — proves attribute priority order

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
route-map PREPEND-OUT permit 10
 set as-path prepend 4040 4040 4040
exit
router bgp 4040
 neighbor 200.40.40.1 route-map PREPEND-OUT out
end
clear ip bgp 200.40.40.1 soft out
```

SSH to E1C (172.20.20.209):
```
configure terminal
route-map PREFER-IAN permit 10
 set local-preference 200
exit
router bgp 1010
 neighbor 200.40.40.2 route-map PREFER-IAN in
end
clear ip bgp 200.40.40.2 soft in
```
Operator runs soft resets manually.

IAN AS-path = 4 hops. IBN AS-path = 1 hop. IAN LP = 200. IBN LP = 100 (default). LP wins → IAN preferred.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: IAN best path (LP 200) despite longer AS-path (4 vs 1).

**Expected Symptoms**

- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IAN best (LP 200), IBN not best (LP 100)
- IAN path shows long AS-path but LP overrides
- Agent demonstrates: Local Preference (#2) evaluated before AS-path (#4)

**Root Cause**

(Intentional test scenario.) Local Preference (200) on IAN routes overrides the longer AS-path (4 hops vs IBN's 1), demonstrating attribute priority in BGP path selection.

**Expected Fix** (teardown only)

Remove both configurations on E1C and IAN.

**Teardown**

On E1C:
```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 route-map PREFER-IAN in
no route-map PREFER-IAN permit 10
end
clear ip bgp 200.40.40.2 soft in
```
On IAN:
```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 route-map PREPEND-OUT out
no route-map PREPEND-OUT permit 10
end
clear ip bgp 200.40.40.1 soft out
```

---

### BGP-027: Conditional Default-Originate

**Concept**: `neighbor X default-originate route-map Y` only sends the default if the route-map condition is satisfied (i.e., a specific prefix exists in the routing table). If the condition prefix is absent, no default is sent — even if the BGP session is Established.
**Difficulty**: Complex
**Devices**: IAN
**SLA Impact**: A1C_TO_X1C (E1C→IAN path — conditional default fails)

**Setup (Break)**

SSH to IAN (172.20.20.220):
```
configure terminal
ip prefix-list CHECK-ROUTE permit 203.0.113.0/24
route-map COND-CHECK permit 10
 match ip address prefix-list CHECK-ROUTE
exit
router bgp 4040
 no neighbor 200.40.40.1 default-originate
 neighbor 200.40.40.1 default-originate route-map COND-CHECK
end
```
The condition checks for 203.0.113.0/24 in IAN's routing table. This prefix does not exist → condition fails → no default is sent to E1C.

**Verify Break**

On IAN:
```
show ip bgp neighbors 200.40.40.1 | include default-originate|route-map
```
Expected: default-originate with COND-CHECK route-map shown.

On E1C:
```
show ip bgp 0.0.0.0
```
Expected: IAN path (200.40.40.2) absent; only IBN path present (if IBN still sends unconditional default).

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — IAN session Established but 0 prefixes (or reduced)
- `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IAN default absent
- `get_bgp(IAN, "config")` — conditional default-originate with COND-CHECK route-map
- `get_routing(IAN, prefix="203.0.113.0/24")` — prefix absent → condition fails → no default sent
- Agent traces: session up, no default from IAN, IAN uses conditional originate, condition not met

**Root Cause**

IAN has a conditional `default-originate route-map COND-CHECK` that only advertises the default route to E1C when 203.0.113.0/24 is present in IAN's routing table; this prefix does not exist, so the condition fails and no default is sent.

**Expected Fix**

Agent proposes on **IAN** (revert to unconditional default-originate):
```
router bgp 4040
 no neighbor 200.40.40.1 default-originate route-map COND-CHECK
 neighbor 200.40.40.1 default-originate
```

**Teardown**

```
configure terminal
router bgp 4040
 no neighbor 200.40.40.1 default-originate route-map COND-CHECK
 neighbor 200.40.40.1 default-originate
no route-map COND-CHECK permit 10
no ip prefix-list CHECK-ROUTE permit 203.0.113.0/24
end
```

---

### BGP-028: Soft Reset Required After Policy Change (Procedural Test)

**Concept**: Inbound BGP policies only take effect after a soft reset. This test validates that the agent correctly identifies when a policy is configured but not yet active, and advises the operator to run `clear ip bgp soft in` manually.
**Difficulty**: Medium
**Devices**: E1C
**SLA Impact**: Policy inactive — IAN routes still accepted (soft reset not run)

**Setup (Break)**

SSH to E1C (172.20.20.209):
```
configure terminal
ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
router bgp 1010
 neighbor 200.40.40.2 prefix-list BLOCK-DEFAULT in
end
```
**Do NOT run `clear ip bgp 200.40.40.2 soft in`.** The prefix-list is configured but the existing session has not been refreshed — old routes (including the default) are still in E1C's BGP table from before the policy was applied.

**Verify Break**

On E1C:
```
show ip bgp 0.0.0.0
show ip bgp neighbors 200.40.40.2 | include prefix-list
```
Expected: Default route from IAN is **still present** (soft reset not performed); prefix-list shows as configured but policy not yet enforced on existing prefixes.

**Expected Symptoms**

- `get_bgp(E1C, "summary")` — IAN Established, prefixes still present (policy not active)
- `get_routing_policies(E1C)` — BLOCK-DEFAULT prefix-list configured on 200.40.40.2 inbound
- But: `get_bgp(E1C, "routing", prefix="0.0.0.0/0")` — IAN default route still accepted (policy inactive)
- Agent identifies: policy configured but soft reset not run → routes not re-evaluated
- Agent must advise operator to run `clear ip bgp 200.40.40.2 soft in` manually (FORBIDDEN in MCP)

**Root Cause**

E1C has an inbound prefix-list (BLOCK-DEFAULT) configured for neighbor 200.40.40.2, but a BGP soft reset has not been performed; the policy is configured but not yet active — existing routes were accepted before the policy was applied and are not re-evaluated until a soft reset occurs.

**Expected Fix**

Agent cannot push the soft reset via `push_config` (FORBIDDEN set). Agent proposes:
1. No config change needed — policy is already configured correctly
2. Advise operator to run on E1C: `clear ip bgp 200.40.40.2 soft in`

> **What the agent should NOT do**: propose re-applying the prefix-list (already there), or push `clear ip bgp` via push_config (FORBIDDEN).

**Teardown**

```
configure terminal
router bgp 1010
 no neighbor 200.40.40.2 prefix-list BLOCK-DEFAULT in
no ip prefix-list BLOCK-DEFAULT seq 5 deny 0.0.0.0/0
no ip prefix-list BLOCK-DEFAULT seq 10 permit 0.0.0.0/0 le 32
end
clear ip bgp 200.40.40.2 soft in
```

---

*End of OSPF & BGP Protocol Troubleshooting Test Suite — 27 OSPF tests + 28 BGP tests = 55 total*
