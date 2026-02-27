# Top Lessons Learned

Curated from resolved cases. Agent updates this file after each case closure.
Read this file at session start. For detailed case history, refer to Jira tickets.

Maximum 20 entries. Each entry: one actionable lesson in 1-2 lines.

### Promotion Criteria
A lesson belongs here if it: (1) applies broadly to future cases, (2) corrects a methodology mistake, and (3) isn't already captured above.

---

1. **Source-first on SLA failure**: When an SLA path fails, always run `get_interfaces(source_device)` immediately. A shutdown `source_interface` (from paths.json) is immediately identifiable and is the root cause — do not escalate to protocol-level investigation until source device interfaces are confirmed Up/Up.

2. **Always pass `source_ip` in traceroute for SLA paths**: Without a source IP, traceroute may succeed via an alternate path and mask the actual monitored-path failure. Always use `traceroute(source_device, destination_ip, source=source_ip)` when `source_ip` is defined in paths.json.

3. **OSPF network type mismatch prevents adjacency formation**: When one peer is configured as POINT_TO_MULTIPOINT and the other as POINT_TO_POINT, the timers automatically differ (hello 30/dead 120 vs 10/40) and neighbors never appear despite L3 reachability. Inspect `get_ospf(device, "interfaces")` network type on both sides; fix the misconfigured side back to standard POINT_TO_POINT—never match the outlier. This is the most common OSPF point-to-point adjacency failure after timer mismatches.

4. **LSDB vs RIB mismatch → adjacency or config issue**: If LSAs present in database but routes missing from RIB, root cause is OSPF adjacency failure or config error, not LSA flooding. Check neighbor states before investigating SPF calculations.

5. **Administratively shutdown interfaces on egress/destination devices break SLA paths silently**: When ISP-facing or egress interfaces are shut down on the destination device, the SLA source receives explicit rejection (host unreachable) rather than timeout. This localizes the issue to the destination device quickly. Always check interface status on egress_devices in paths.json, not just the source device. Both source and destination interfaces must be Up/Up for SLA paths to work.

6. **OSPF timer mismatch is a silent killer in multi-vendor networks**: Mismatched hello/dead intervals between OSPF neighbors prevent adjacency formation despite physical connectivity and layer 3 reachability working correctly. With mixed vendors (Arista EOS vs Cisco IOS), explicit timer alignment is critical — Arista defaults to hello 33, Cisco to hello 10. Zero neighbors on a healthy up/up interface with layer 3 connectivity = suspect timer mismatch; inspect `get_ospf(device, "interfaces")` hello/dead intervals on both sides.

7. **ABR is a critical single point of failure for multi-area networks**: When an ABR lacks backbone adjacencies (Area 0), all downstream areas lose inter-area routes and external routes simultaneously. A single misconfigured or broken ABR cascades failures across multiple SLA paths and leaf devices. Monitor ABR state aggressively; ABR backbone adjacencies are prerequisites for all stub/NSSA area functionality.

8. **Stale LSA age in LSDB indicates broken originating router adjacencies**: When Type 3 or Router LSAs appear in the LSDB with age 1500+ seconds (25+ minutes) and remain stale (not incrementing toward max-age or refreshing), the originating router (especially ABR) likely has broken inter-area adjacencies preventing proper LSA refresh. This pattern indicates ABR connectivity failure rather than LSDB flooding issues. Compare LSA age across neighbors; identical ages across multiple neighbors suggests stale advertisement from source.

9. **OSPF passive-interface silently blocks adjacencies**: Passive-interface prevents hello/hello exchange but leaves the physical link and layer 3 connectivity appearing healthy. Result: interface up/up, layer 3 reachable, but neighbor count zero. Always inspect `get_ospf(device, "interfaces")` for `passive` flag when neighbors are absent despite correct parameters (timers, area, auth, network type). This is especially critical on ABRs where passive Area N interfaces prevent inter-area route propagation.

10. **ABR Area 0 interface timer verification is mandatory when inter-area routes vanish**: When inter-area routes (especially to NSSA/stub areas) suddenly disappear while OSPF Area 1 neighbors remain healthy, suspect broken ABR→Area 0 adjacencies caused by timer mismatch. Verify ABR's Area 0 interface dead-intervals match peer routers' (typically 40 sec on Cisco). Dead-intervals of 101/103/30 or other non-standard values prevent neighbor formation on point-to-point links despite up/up interfaces and layer 3 reachability. If `get_ospf(abr, "neighbors")` shows zero neighbors on Area 0 interfaces, always run `show ip ospf interface <interface>` to inspect timers before investigating LSDB or redistribution. Mismatched Area 0 timers cascade to all downstream areas losing both inter-area and external routes.

11. **OSPF EXCHSTART stuck state → check MTU mismatch first**: When OSPF neighbors appear but are stuck in EXCHSTART (not progressing to FULL), MTU mismatch is the most common cause. Hellos (small) succeed but DBD packets (larger) fail or corrupt, halting adjacency. Always compare interface MTU on both sides of a stuck EXCHSTART link (e.g., `show interface X` MTU field). Standard Ethernet IP MTU is 1500 bytes; values like 1400 are non-standard and deviate. Fix the non-standard side, not the peer. If timers and authentication match but EXCHSTART persists, MTU is the next check.
