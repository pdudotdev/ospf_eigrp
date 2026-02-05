# ✨ Troubleshooting CCNP Concepts with AI & MCP ✨

[![Last Commit](https://img.shields.io/github/last-commit/pdudotdev/netaimcp)](https://github.com/pdudotdev/netaimcp/commits/main/)

## 📖 Table of Contents
- 🔥 **Troubleshooting Networks with Claude and MCP**
  - [🔍 Overview](#-overview)
  - [⚒️ Tech Stack]()
  - [📋 Included Vendors]()
  - [🎓 Networking Topics]()
  - [🔄 Network Topology]()
  - [🧪 Automation and Troubleshooting Tests]()
  - [⬆️ Planned Upgrades](#-planned-upgrades)
  - [⚠️ Disclaimer](#-disclaimer)
  - [📜 License](#-license)

## 🔍 Overview
The purpose of this project is to showcase the capabilities of **Claude AI** and **MCP**, combined with **Python** and **Scrapli**, in regards to network automation and troubleshooting.

By design, the project is **multi-vendor**, **multi-protocol**, **multi-area/multi-AS**, **OSI L3-focused**, in order to automate and troubleshoot various scenarios in a diverse and complex network.

I am **NOT** going to explain here how to build the topology | write the MCP server in Python | enhance the MCP server with new tools. I already did that from scratch in my beginner-friendly [**Udemy course**](https://www.udemy.com/course/mcp-server/?referralCode=D62613A8194D2D915B55). Feel free to join to get instructor support, regular updates, access to Discord etc.

However, I am providing the **topology diagram**, the **startup config** of each router, as well as the actual **Containerlab YAML file** defining the network.

⚠️ **NOTE**: This project assumes at least **CCNA**-level knowledge (**CCNP** preferred), as well as familiarity with **Linux** terminal commands, **Python** syntax, and multi-vendor **CLIs**.

🍀 **NOTE**: This is an evolving project, with new features being added periodically, so feel free to check back once in a while.

## ⚒️ Tech Stack
The main tools and technologies used for building the project:
- [x] Claude AI (Claude Code)
- [x] MCP Server (FastMCP)
- [x] ContainerLab
- [x] Docker
- [x] Python
- [x] Scrapli
- [x] VS Code
- [x] Ubuntu 24
- [x] VirtualBox/VMware

## 📋 Included Vendors
- [x] Arista: EOS (cEOS)
- [x] Cisco: IOS/IOS-XE (IOL)

## 🎓 Networking Topics
Network concepts currently in this topology:
- [x] OSPF multi-area:
  - Basic protocol config
    - Reference bandwidth
    - Point-to-point links
    - Passive interfaces
    - MD5 authentication
    - External type 1 routes
  - Route redistribution
  - Route summarization (ABR)
  - Route filtering with prefix lists
  - Route filtering with distribute lists
  - Area types: normal, totally stubby, totally nssa

- [x] EIGRP:
  - Basic protocol config
    - Passive interfaces
    - MD5 authentication
    - Stub connected/summary
  - Local summarization
  - Route redistribution
  - Default metric via route map

- [x] Others:
  - Policy-Based Routing
  - IP SLA icmp-echo


## 🧪 Planned Upgrades
- [ ] Adding BGP
- [ ] Adding IS-IS
- [ ] Adding new vendors

## ⚠️ Disclaimer
This project is intended for educational purposes only. Users are responsible for building their own lab environment and meeting the necessary conditions (e.g., RAM/vCPU, router OS images, Claude subscription/API key, etc.). Users are responsible for ensuring that their use of this tool complies with all applicable laws and regulations. The developer of this project does not endorse or support any malicious or unauthorized activities. Use this tool responsibly.

## 📜 License
Licensed under the [GNU GENERAL PUBLIC LICENSE Version 3](https://github.com/pdudotdev/netaimcp/blob/main/LICENSE).