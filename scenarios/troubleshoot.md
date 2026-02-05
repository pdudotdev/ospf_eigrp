## Troubleshooting Intro
In this file you'll find troubleshooting scenarios based on the structure discussed in the [README](https://github.com/pdudotdev/netaimcp/tree/main?tab=readme-ov-file#-automation-and-troubleshooting), ranging from basic to more advanced. I will update this list periodically.

⚠️ **NOTE**: Make sure to use `containerlab redeploy -t lab.yml` after each scenario to start clean from the default network configuration.

## 🍀 CCNA-level scenarios

### ▫️ Scenario 1

- [x] **Summary**:
```
R1A OSPF adjacency stuck in EXCHANGE, while R2A is stuck in EXCH START state.
```
- [x] **Causing Failure**: 
```
Changing the MTU on R2A Eth3 to 1400 to cause a mismatch with R1A, using the commands below:

interface Eth3
 mtu 1400
```
- [x] **Confirming Failure**:
```
Checking the effects of the commands above:

R2A(config-if-Et3)#show interfaces eth3 | i MTU
  IP MTU 1400 bytes, BW 1000000 kbit
R2A(config-if-Et3)#show ip ospf neighbor 
Neighbor ID     Instance VRF      Pri State                  Dead Time   Address         Interface
3.3.3.3         1        default  1   FULL                   00:00:35    10.0.0.10       Ethernet4
1.1.1.1         1        default  0   EXCH START             00:00:34    10.0.0.1        Ethernet3
7.7.7.7         1        default  0   FULL                   00:00:34    10.1.1.9        Ethernet2
6.6.6.6         1        default  0   FULL                   00:00:33    10.1.1.13       Ethernet1

R1A#show ip ospf neighbor
Neighbor ID     Instance VRF      Pri State                  Dead Time   Address         Interface
2.2.2.2         1        default  0   EXCHANGE               00:00:32    10.0.0.2        Ethernet4
3.3.3.3         1        default  1   FULL                   00:00:38    10.0.0.6        Ethernet3
11.11.11.11     1        default  1   FULL                   00:00:32    172.16.0.10     Ethernet2
10.10.10.10     1        default  1   FULL                   00:00:30    172.16.0.6      Ethernet1
```
- [x] **User Prompt**:
```
Why is the R1A-R2A OSPF adjacency stuck? Can you check and fix please?
```
- [x] **Commands issued by Claude**:
```
show ip ospf neighbor
show ip ospf interface Ethernet3
show running-config interface Ethernet3
interface Ethernet3
no mtu 1400
```
- [x] **Confirmation**:
```
R2A#show ip ospf neighbor
Neighbor ID     Instance VRF      Pri State                  Dead Time   Address         Interface
3.3.3.3         1        default  1   FULL                   00:00:34    10.0.0.10       Ethernet4
1.1.1.1         1        default  0   FULL                   00:00:38    10.0.0.1        Ethernet3
7.7.7.7         1        default  0   FULL                   00:00:29    10.1.1.9        Ethernet2
6.6.6.6         1        default  0   FULL                   00:00:33    10.1.1.13       Ethernet1 
```

### ▫️ Scenario 2

- [x] **Summary**:
```
R1A and R3C OSPF adjancency is broken.
```
- [x] **Causing Failure**: 
```
Wrong OSPF area number configured on R3C's Eth0/3 interface, using the commands below:

router ospf 1
 network 10.0.0.4 0.0.0.3 area 1
```
- [x] **Confirming Failure**:
```
Checking the effects of the commands above:

R3C#show ip ospf interface Eth0/3 | i Area
  Internet Address 10.0.0.6/30, Interface ID 5, Area 1
R3C#show ip ospf neighbor                  

Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           0   FULL/  -        00:00:37    10.0.0.9        Ethernet1/0
```
- [x] **User Prompt**:
```
R1A and R3C OSPF adjancency seems to be broken. Please take a look and solve the issue.
```
- [x] **Commands issued by Claude**:
```
show ip ospf neighbor
show ip ospf interface Ethernet3
show ip interface brief
show running-config | section router ospf
router ospf 1
no network 10.0.0.4 0.0.0.3 area 1
network 10.0.0.4 0.0.0.3 area 0
```
- [x] **Confirmation**:
```
R3C#show ip ospf neighbor 

Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           0   FULL/  -        00:00:39    10.0.0.9        Ethernet1/0
1.1.1.1           0   FULL/  -        00:00:30    10.0.0.5        Ethernet0/3
```

### ▫️ Scenario 3

- [x] **Summary**:
```
OSPF adjacency between R2A and R3C fails.
```
- [x] **Causing Failure**: 
```
Changing the Hello and Dead timers on R2A to cause a mismatch with R3C, using the commands below:

interface Ethernet4
 ip ospf hello-interval 5
 ip ospf dead-interval 20
```
- [x] **Confirming Failure**:
```
Checking the effects of the commands above:

R2A#show ip ospf interface Ethernet 4
Ethernet4 is up
  Interface Address 10.0.0.9/30, instance 1, VRF default, Area 0.0.0.0
  Network Type Point-To-Point, Cost: 100
  Transmit Delay is 1 sec, State P2P
  Interface Speed: 1000 mbps
  No Designated Router on this network
  No Backup Designated Router on this network
  Timer intervals configured, Hello 5, Dead 20, Retransmit 5
  Neighbor Count is 0
  Message-digest authentication, using key id 1
  Traffic engineering is disabled
  TI-LFA protection is disabled
R2A#show ip ospf neighbor
Neighbor ID     Instance VRF      Pri State                  Dead Time   Address         Interface
1.1.1.1         1        default  0   FULL                   00:00:38    10.0.0.1        Ethernet3
7.7.7.7         1        default  0   FULL                   00:00:29    10.1.1.9        Ethernet2
6.6.6.6         1        default  0   FULL                   00:00:33    10.1.1.13       Ethernet1
```
- [x] **User Prompt**:
```
OSPF neighborship between R2A and R3C fails. Investigate and apply a fix.
```
- [x] **Commands issued by Claude**:
```
show ip ospf neighbor
show ip ospf interface Ethernet4
show running-config interface Ethernet4
interface Ethernet4
no ip ospf hello-interval 5
no ip ospf dead-interval 20
```
- [x] **Confirmation**:
```
R2A#show ip ospf neighbor
Neighbor ID     Instance VRF      Pri State                  Dead Time   Address         Interface
3.3.3.3         1        default  1   FULL                   00:00:34    10.0.0.10       Ethernet4
1.1.1.1         1        default  0   FULL                   00:00:38    10.0.0.1        Ethernet3
7.7.7.7         1        default  0   FULL                   00:00:29    10.1.1.9        Ethernet2
6.6.6.6         1        default  0   FULL                   00:00:33    10.1.1.13       Ethernet1 
```

## 🔥 CCNP-level scenarios

### Scenario 1

- [x] **Summary**:
```
Routers don't have a summary route to R9C's Loopback interfaces, instead they show separate entries for each Loopback in their routing tables.
```
- [x] **Causing Failure**: 
```
Omitting to advertise summary routes on R9C (EIGRP stub) to its R8C neighbor, using the commands below:

R9C(config)interface Ethernet0/1
R9C(config-if)ip summary-address eigrp 20 9.9.0.0 255.255.252.0
R9C(config)#router eigrp 20
R9C(config-router)#eigrp stub connected
```
- [x] **Confirming Failure**:
```
Checking the effects of the commands above, on R1A:

R1A#show ip route
<...>
 O E1     9.9.1.0/24 [110/320]
           via 10.0.0.2, Ethernet4
 O E1     9.9.2.0/24 [110/320]
           via 10.0.0.2, Ethernet4
 O E1     9.9.3.0/24 [110/320]
           via 10.0.0.2, Ethernet4
```
- [x] **User Prompt**:
```
Why are all routers in the network showing individual routes to R9C's loopbacks. Check this and give me all potential fixes to choose from.
```
- [x] **Commands issued by Claude**:
```
show ip route | include 9.9.9
show ip route eigrp | include 9.9.9
show ip interface brief | include Loopback
show running-config | section router eigrp
show running-config | section router ospf
show running-config | include redistribute
show ip ospf database external
show ip eigrp neighbors detail
show ip eigrp topology
```

```
Root Cause

R9C is configured as: eigrp stub connected

This tells R9C to advertise its connected routes (the loopback /24s). Even though ip summary-address eigrp 20 9.9.0.0 255.255.252.0 is configured on interface Et0/1, the stub connected configuration is causing it to still advertise the individual connected routes.

Fix Options

Option 1: Change Stub to Summary (Recommended)

Location: R9C
Result: Advertises only the summary route, suppresses component routes
Impact: R9C will stop advertising individual loopbacks

Option 2: Add Summary to Stub

Location: R9C
Result: Advertises both connected AND summary routes (summary should be preferred by R8C due to better metric)
Impact: Both routes present in EIGRP, but routing table should prefer summary

Option 3: Summarize at ASBR (R8C)

Location: R8C
Result: Individual routes enter OSPF from EIGRP, but get summarized before propagating
Impact: Fixes OSPF domain, doesn't fix EIGRP domain

Which approach would you like to take?
```

```
Let's go with option 2.
```

```
router eigrp 20
eigrp stub connected summary
```

- [x] **Confirmation**:
```
R1A#show ip route
<...>
 O E1     9.9.0.0/22 [110/320]
           via 10.0.0.2, Ethernet4
```
