📄 CASE NO. - 00001-R10C-SLA
Date: YYYY-MM-DD HH:MM UTC
Device(s): R10C

🔹 Reported Issue:
  - Router R2C lost its R3C neighbor

🔹 All Commands Used To Isolate Issue:
  - show ip ospf neighbor
  - show ip interface brief
  - show ip ospf interface Ethernet0/1
  - show ip route

🔹 Commands That Actually Identified the Issue:
  - show ip ospf neighbor
  - show ip ospf interface Ethernet0/1

🔹 Proposed Fixes (Per Device):
  - Setting OSPF hello-interval to default value on R2C's interface Ethernet0/1

🔹 Commands Used Upon User Approval:
  interface Ethernet0/1
   default ip ospf hello-interval

🔹 Post-Fix State:
  - OSPF adjacency restored (FULL)

🔹 Verification: PASSED
🔹 Case Status: FIXED

📋 CASE METADATA

🔸 Case Handling Plan:


🔸 Lessons Learned:

