## Regression Checklist (Manual Tests Performed by User)

Run this checklist after any significant change to `MCPServer.py`, `oncall_watcher.py`,
`platforms/platform_map.py`, or any skill file:

| # | Check | Method |
|---|-------|--------|
| 1 | Unit tests pass | `./run_tests.sh unit` |
| 2 | Integration tests pass | `./run_tests.sh integration` |
| 3 | OSPF adjacency diagnosis works | ST-001 |
| 4 | EIGRP passive-interface diagnosis works | ST-002 |
| 5 | Redistribution diagnosis works | ST-003 |
| 6 | Policy-based routing diagnosis works | ST-004 |
| 7 | EIGRP stub configuration works | ST-005 |
| 8 | On-Call agent invoked and diagnoses correctly | OC-001 |
| 9 | On-Call watcher log interactions | WB-001 - WB-003 |
| 10 | Maintenance windows policy check | MW-001 |

**NOTE:** All Standalone or On-Call cases are documented in `cases.md` | Post-test check |