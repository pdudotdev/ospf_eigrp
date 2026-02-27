# 📁 Project File & Directory Reference

A structured overview of the key files, services, and directories that power the troubleshooting environment.

---

## ✅ `lessons.md`

**Purpose:** Institutional memory file.

A curated list (maximum 20 entries) of lessons learned from past troubleshooting cases:

- Common gotchas  
- Recurring patterns  
- “We see this one a lot” issues  

After every On-Call session, the agent:
1. Reads this file  
2. Decides whether to add a new lesson  
3. Or replace an older one with something more broadly useful  

> Think of it as the team’s cheat sheet for avoiding the same mistake twice.

---

## ✅ `intent.json`

**Purpose:** Source of truth for network design.

Defines the big-picture architecture:

- Area Border Routers (ABRs)  
- EIGRP / OSPF / BGP speakers  
- Autonomous Systems  
- OSPF areas  
- Peering relationships  
- NAT design expectations  

When troubleshooting, this is your starting point.  
It helps answer: *“Is this device supposed to be doing X?”*

---

## ✅ `network.json`  
*(inventory/NETWORK.json)*

**Purpose:** Device roster and connection metadata.

Stores management details for every device:

- SSH / API host  
- CLI style (Cisco IOS, Arista EOS, MikroTik RouterOS)  
- Transport method (SSH, HTTPS, REST)  
- Physical location  

When you want to talk to a device, this file tells the tools **how to connect**.

---

## ✅ `platform_map.py`

**Purpose:** Vendor command abstraction layer.

Acts as the translator between human intent and vendor-specific commands.

Example:
```
get_ospf(device="R3C", query="neighbors")
```

This file converts that generic call into:
- The correct Cisco IOS CLI command  
- Or Arista EOS syntax  
- Or MikroTik RouterOS command  
- Or the proper REST API call  

It lets you forget about vendor dialect differences.

---

## ✅ `mcp_tool_map.json`

**Purpose:** MCP tool capability reference.

Maps which MCP tool handles which command.

Instead of guessing whether to use `run_show`:
- Check if `get_ospf`, `get_routing`, or another specialized tool exists.

Important behavior:
- If a tool returns empty → the feature is not configured.
- It does **not** mean the query is unsupported.

Prevents unnecessary fallback commands.

---

## ✅ `maintenance.json`

**Purpose:** Change control policy (read-only).

Defines approved configuration windows:

- Monday–Friday  
- 06:00–18:00 UTC  

Outside these hours:
- Config pushes are blocked automatically.

Prevents accidental changes during critical business hours.

---

## ✅ `skills/` (folder)

**Purpose:** Troubleshooting playbooks.

Each file contains a symptom-first decision tree for:

- OSPF  
- EIGRP  
- BGP  
- Redistribution  
- Routing policy  
- On-Call mode  

Written in plain language with:
- Checklists  
- Tables  
- Investigation flows  

Use after ruling out basic interface/neighbor issues.  
These guide deeper inspection (LSDB, route-maps, policies, etc.).

---

## ✅ `paths.json`  
*(located in `sla_paths/`)*

**Purpose:** IP SLA monitoring definitions.

Defines:

- Source IP  
- Destination IP  
- Expected device path  

When an SLA path fails:
1. `oncall_watcher` looks up details here  
2. Determines what should be reachable  
3. Hands off investigation to you  

---

## ✅ `CLAUDE.md`

**Purpose:** The project bible.

Contains:

- 6-principle troubleshooting methodology  
- Standalone & On-Call workflows  
- Complete MCP tool list  
- Lessons curation process  
- Case management workflow  
- 11 common pitfalls to avoid  

Everything the agent needs to operate lives here.

---

## ✅ `jira_client.py`

**Purpose:** Jira Service Management integration.

An async REST client that:

- Logs findings  
- Posts resolution comments  
- Updates Jira tickets  

It bridges troubleshooting sessions with the ticketing system.

---

## ✅ `MCPServer.py`

**Purpose:** FastMCP tool server.

Exposes all troubleshooting tools:

- `get_ospf`  
- `get_eigrp`  
- `get_bgp`  
- `get_routing`  
- `ping`  
- `traceroute`  
- `push_config` 
- etc.

Workflow:
1. Receives tool call  
2. Uses `platform_map.py` for vendor translation  
3. Executes command  
4. Parses output  
5. Returns structured data  

---

## ✅ `oncall_watcher.py`

**Purpose:** Automated SLA monitoring sentry.

Monitors Syslog for SLA failure alerts.

When triggered:
1. Creates a Jira ticket  
2. Injects issue key into Claude prompt  
3. Starts troubleshooting session  

Acts as the handoff from passive monitoring to active investigation.

---

## ✅ `oncall_watcher.log`

**Purpose:** Watcher activity log.

Records:

- SLA failures detected  
- Jira tickets created  
- Sessions started  

Useful for:
- Debugging watcher issues  
- Reviewing historical alert patterns  