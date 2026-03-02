# IT-003 — MCP Tool Test Results
*Generated: 2026-03-02 16:15:33 UTC*

## IT-003a: Platform Connectivity

### test_connectivity_ios (R3C — SSH)
```json
{
  "device": "R3C",
  "cli_style": "ios",
  "cache_hit": false,
  "parsed": {
    "version": {
      "version_short": "17.16",
      "platform": "Linux",
      "version": "17.16.1a",
      "image_id": "X86_64BI_LINUX-ADVENTERPRISEK9-M",
      "label": "RELEASE SOFTWARE (fc1)",
      "os": "IOS",
      "location": "IOSXE",
      "image_type": "production image",
      "copyright_years": "1986-2024",
      "compiled_date": "Thu 19-Dec-24 17:54",
      "compiled_by": "mcpre",
      "rom": "Bootstrap program is Linux",
      "hostname": "R3C",
      "uptime": "6 hours, 9 minutes",
      "system_restarted_at": "10:06:03 UTC Mon Mar 2 2026",
      "system_image": "unix:/iol/iol.bin",
      "last_reload_reason": "Unknown reason",
      "chassis_sn": "14",
      "number_of_intfs": {
        "Ethernet": "8"
      },
      "processor_board_flash": "1024K",
      "curr_config_register": "0x0"
    }
  }
}
```

### test_connectivity_eos (R1A — eAPI)
```json
{
  "device": "R1A",
  "cli_style": "eos",
  "cache_hit": false,
  "parsed": [
    {
      "mfgName": "Arista",
      "modelName": "cEOSLab",
      "hardwareRevision": "",
      "serialNumber": "88F838957495E4CE2476B8BA54D6510D",
      "systemMacAddress": "00:1c:73:a4:d7:d8",
      "hwMacAddress": "00:00:00:00:00:00",
      "configMacAddress": "00:00:00:00:00:00",
      "version": "4.35.0F-44178984.4350F (engineering build)",
      "architecture": "x86_64",
      "internalVersion": "4.35.0F-44178984.4350F",
      "internalBuildId": "33b708fe-8b04-48db-bb84-7f77a6b3cc66",
      "imageFormatVersion": "1.0",
      "imageOptimization": "None",
      "kernelVersion": "6.17.0-14-generic",
      "bootupTimestamp": 1772445957.4263723,
      "uptime": 22165.943242311478,
      "memTotal": 32819000,
      "memFree": 16865116,
      "isIntlVersion": false
    }
  ]
}
```

### test_connectivity_ros (R18M — REST)
```json
{
  "device": "R18M",
  "cli_style": "routeros",
  "cache_hit": false,
  "parsed": [
    {
      ".id": "*2018A000",
      "bgp": "true",
      "distance": "20",
      "dst-address": "0.0.0.0/0",
      "dynamic": "true",
      "gateway": "220.50.50.1",
      "immediate-gw": "220.50.50.1%ether3",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B000",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "0.0.0.0/0",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018C040",
      "distance": "110",
      "dst-address": "0.0.0.0/0",
      "dynamic": "true",
      "gateway": "172.16.77.1%ether4",
      "immediate-gw": "172.16.77.1%ether4",
      "inactive": "false",
      "ospf": "true",
      "routing-table": "main",
      "scope": "20",
      "target-scope": "10"
    },
    {
      ".id": "*201830B0",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "18.18.18.0/24",
      "dynamic": "true",
      "gateway": "lo1",
      "immediate-gw": "lo1",
      "inactive": "false",
      "local-address": "18.18.18.1%lo1",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*2018C000",
      "active": "true",
      "distance": "110",
      "dst-address": "19.19.19.0/24",
      "dynamic": "true",
      "gateway": "172.16.77.1%ether4",
      "immediate-gw": "172.16.77.1%ether4",
      "inactive": "false",
      "ospf": "true",
      "routing-table": "main",
      "scope": "20",
      "target-scope": "10"
    },
    {
      ".id": "*2018C010",
      "active": "true",
      "distance": "110",
      "dst-address": "20.20.20.0/24",
      "dynamic": "true",
      "gateway": "172.16.77.6%ether5",
      "immediate-gw": "172.16.77.6%ether5",
      "inactive": "false",
      "ospf": "true",
      "routing-table": "main",
      "scope": "20",
      "target-scope": "10"
    },
    {
      ".id": "*20183090",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "172.16.77.0/30",
      "dynamic": "true",
      "gateway": "ether4",
      "immediate-gw": "ether4",
      "inactive": "false",
      "local-address": "172.16.77.2%ether4",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*201830A0",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "172.16.77.4/30",
      "dynamic": "true",
      "gateway": "ether5",
      "immediate-gw": "ether5",
      "inactive": "false",
      "local-address": "172.16.77.5%ether5",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*2018C020",
      "active": "true",
      "distance": "110",
      "dst-address": "172.16.77.8/30",
      "dynamic": "true",
      "ecmp": "true",
      "gateway": "172.16.77.1%ether4",
      "immediate-gw": "172.16.77.1%ether4",
      "inactive": "false",
      "ospf": "true",
      "routing-table": "main",
      "scope": "20",
      "target-scope": "10"
    },
    {
      ".id": "*2018C030",
      "active": "true",
      "distance": "110",
      "dst-address": "172.16.77.8/30",
      "dynamic": "true",
      "ecmp": "true",
      "gateway": "172.16.77.6%ether5",
      "immediate-gw": "172.16.77.6%ether5",
      "inactive": "false",
      "ospf": "true",
      "routing-table": "main",
      "scope": "20",
      "target-scope": "10"
    },
    {
      ".id": "*80000001",
      "active": "true",
      "distance": "1",
      "dst-address": "172.20.20.0/24",
      "dynamic": "false",
      "gateway": "172.31.255.29",
      "immediate-gw": "172.31.255.29%ether1",
      "inactive": "false",
      "routing-table": "main",
      "scope": "30",
      "static": "true",
      "target-scope": "10"
    },
    {
      ".id": "*20183060",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "172.31.255.28/30",
      "dynamic": "true",
      "gateway": "ether1",
      "immediate-gw": "ether1",
      "inactive": "false",
      "local-address": "172.31.255.30%ether1",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*2018B010",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.40.40.0/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B020",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.40.40.4/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018A030",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.50.50.0/30",
      "dynamic": "true",
      "gateway": "220.50.50.1",
      "immediate-gw": "220.50.50.1%ether3",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B050",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.50.50.0/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018A040",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.50.50.4/30",
      "dynamic": "true",
      "gateway": "220.50.50.1",
      "immediate-gw": "220.50.50.1%ether3",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B060",
      "bgp": "true",
      "distance": "20",
      "dst-address": "200.50.50.4/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*20183070",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "220.40.40.0/30",
      "dynamic": "true",
      "gateway": "ether2",
      "immediate-gw": "ether2",
      "inactive": "false",
      "local-address": "220.40.40.2%ether2",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*2018B030",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.40.40.0/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B040",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.40.40.4/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*20183080",
      "active": "true",
      "connect": "true",
      "distance": "0",
      "dst-address": "220.50.50.0/30",
      "dynamic": "true",
      "gateway": "ether3",
      "immediate-gw": "ether3",
      "inactive": "false",
      "local-address": "220.50.50.2%ether3",
      "routing-table": "main",
      "scope": "10",
      "target-scope": "5"
    },
    {
      ".id": "*2018A010",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.50.50.0/30",
      "dynamic": "true",
      "gateway": "220.50.50.1",
      "immediate-gw": "220.50.50.1%ether3",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B070",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.50.50.0/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018A020",
      "active": "true",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.50.50.4/30",
      "dynamic": "true",
      "gateway": "220.50.50.1",
      "immediate-gw": "220.50.50.1%ether3",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    },
    {
      ".id": "*2018B080",
      "bgp": "true",
      "distance": "20",
      "dst-address": "220.50.50.4/30",
      "dynamic": "true",
      "gateway": "220.40.40.1",
      "immediate-gw": "220.40.40.1%ether2",
      "inactive": "false",
      "routing-table": "main",
      "scope": "40",
      "target-scope": "10"
    }
  ]
}
```

## IT-003b: Protocol Tools

### test_ospf_eos (R1A — eAPI)
```json
{
  "device": "R1A",
  "cli_style": "eos",
  "cache_hit": false,
  "parsed": [
    {
      "vrfs": {
        "default": {
          "instList": {
            "1": {
              "ospfNeighborEntries": [
                {
                  "routerId": "2.2.2.2",
                  "interfaceAddress": "10.0.0.2",
                  "interfaceName": "Ethernet4",
                  "priority": 1,
                  "adjacencyState": "full",
                  "drState": null,
                  "options": {
                    "multitopologyCapability": false,
                    "externalRoutingCapability": true,
                    "multicastCapability": false,
                    "nssaCapability": false,
                    "linkLocalSignaling": false,
                    "demandCircuitsSupport": false,
                    "opaqueLsaSupport": false,
                    "doNotUseInRouteCalc": false
                  },
                  "inactivity": 1772468159.3946738,
                  "details": {
                    "areaId": "0.0.0.0",
                    "designatedRouter": "0.0.0.0",
                    "backupDesignatedRouter": "0.0.0.0",
                    "numberOfStateChanges": 7,
                    "stateTime": 1772446059.394709,
                    "inactivityDefers": 0,
                    "retransmissionCount": 4,
                    "bfdState": "adminDown",
                    "bfdRequestSent": false,
                    "grHelperTimer": null,
                    "grNumAttempts": 0,
                    "grLastRestartTime": null
                  }
                },
                {
                  "routerId": "3.3.3.3",
                  "interfaceAddress": "10.0.0.6",
                  "interfaceName": "Ethernet3",
                  "priority": 1,
                  "adjacencyState": "full",
                  "drState": null,
                  "options": {
                    "multitopologyCapability": false,
                    "externalRoutingCapability": true,
                    "multicastCapability": false,
                    "nssaCapability": false,
                    "linkLocalSignaling": false,
                    "demandCircuitsSupport": false,
                    "opaqueLsaSupport": false,
                    "doNotUseInRouteCalc": false
                  },
                  "inactivity": 1772468155.3948417,
                  "details": {
                    "areaId": "0.0.0.0",
                    "designatedRouter": "0.0.0.0",
                    "backupDesignatedRouter": "0.0.0.0",
                    "numberOfStateChanges": 7,
                    "stateTime": 1772446061.3948498,
                    "inactivityDefers": 0,
                    "retransmissionCount": 3,
                    "bfdState": "adminDown",
                    "bfdRequestSent": false,
                    "grHelperTimer": null,
                    "grNumAttempts": 0,
                    "grLastRestartTime": null
                  }
                },
                {
                  "routerId": "11.11.11.11",
                  "interfaceAddress": "172.16.0.10",
                  "interfaceName": "Ethernet2",
                  "priority": 1,
                  "adjacencyState": "full",
                  "drState": null,
                  "options": {
                    "multitopologyCapability": false,
                    "externalRoutingCapability": false,
                    "multicastCapability": false,
                    "nssaCapability": false,
                    "linkLocalSignaling": false,
                    "demandCircuitsSupport": false,
                    "opaqueLsaSupport": false,
                    "doNotUseInRouteCalc": false
                  },
                  "inactivity": 1772468158.3949373,
                  "details": {
                    "areaId": "0.0.0.2",
                    "designatedRouter": "0.0.0.0",
                    "backupDesignatedRouter": "0.0.0.0",
                    "numberOfStateChanges": 7,
                    "stateTime": 1772446064.394945,
                    "inactivityDefers": 0,
                    "retransmissionCount": 0,
                    "bfdState": "adminDown",
                    "bfdRequestSent": false,
                    "grHelperTimer": null,
                    "grNumAttempts": 0,
                    "grLastRestartTime": null
                  }
                },
                {
                  "routerId": "10.10.10.10",
                  "interfaceAddress": "172.16.0.6",
                  "interfaceName": "Ethernet1",
                  "priority": 1,
                  "adjacencyState": "full",
                  "drState": null,
                  "options": {
                    "multitopologyCapability": false,
                    "externalRoutingCapability": false,
                    "multicastCapability": false,
                    "nssaCapability": false,
                    "linkLocalSignaling": false,
                    "demandCircuitsSupport": false,
                    "opaqueLsaSupport": false,
                    "doNotUseInRouteCalc": false
                  },
                  "inactivity": 1772468162.3950276,
                  "details": {
                    "areaId": "0.0.0.2",
                    "designatedRouter": "0.0.0.0",
                    "backupDesignatedRouter": "0.0.0.0",
                    "numberOfStateChanges": 7,
                    "stateTime": 1772446060.395035,
                    "inactivityDefers": 0,
                    "retransmissionCount": 2,
                    "bfdState": "adminDown",
                    "bfdRequestSent": false,
                    "grHelperTimer": null,
                    "grNumAttempts": 0,
                    "grLastRestartTime": null
                  }
                }
              ]
            }
          }
        }
      }
    }
  ]
}
```

### test_eigrp_ios (R3C — SSH)
```json
{
  "device": "R3C",
  "cli_style": "ios",
  "cache_hit": false,
  "parsed": {
    "eigrp_instance": {
      "10": {
        "vrf": {
          "default": {
            "address_family": {
              "ipv4": {
                "name": "",
                "named_mode": false,
                "eigrp_interface": {
                  "Ethernet0/1": {
                    "eigrp_nbr": {
                      "192.168.10.6": {
                        "peer_handle": 1,
                        "hold": 13,
                        "uptime": "04:05:55",
                        "srtt": 0.003,
                        "rto": 100,
                        "q_cnt": 0,
                        "last_seq_number": 39
                      }
                    }
                  },
                  "Ethernet0/2": {
                    "eigrp_nbr": {
                      "192.168.10.2": {
                        "peer_handle": 0,
                        "hold": 11,
                        "uptime": "04:05:55",
                        "srtt": 1.573,
                        "rto": 5000,
                        "q_cnt": 0,
                        "last_seq_number": 38
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### test_bgp_ros (R18M — REST)
```json
{
  "device": "R18M",
  "cli_style": "routeros",
  "cache_hit": false,
  "parsed": [
    {
      ".id": "*1",
      "as": "2020",
      "inactive": "false",
      "instance": "default",
      "local.default-address": "220.40.40.2",
      "local.role": "ebgp",
      "name": "TO-R14C",
      "remote.address": "220.40.40.1",
      "remote.as": "4040",
      "routing-table": "main"
    },
    {
      ".id": "*2",
      "as": "2020",
      "inactive": "false",
      "instance": "default",
      "local.default-address": "220.50.50.2",
      "local.role": "ebgp",
      "name": "TO-R17C",
      "remote.address": "220.50.50.1",
      "remote.as": "5050",
      "routing-table": "main"
    }
  ]
}
```

### test_interfaces_ros (R19M — REST)
```json
{
  "device": "R19M",
  "cli_style": "routeros",
  "cache_hit": false,
  "parsed": [
    {
      ".id": "*2",
      "actual-mtu": "1500",
      "default-name": "ether1",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:14",
      "link-downs": "0",
      "mac-address": "0C:00:E6:1F:95:00",
      "mtu": "1500",
      "name": "ether1",
      "running": "true",
      "rx-byte": "60987",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "887",
      "tx-byte": "2781511",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "10166",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*3",
      "actual-mtu": "1500",
      "comment": "TO-R18M",
      "default-name": "ether2",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:14",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:DE:84:27",
      "mtu": "1500",
      "name": "ether2",
      "running": "true",
      "rx-byte": "743208",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "5809",
      "tx-byte": "873433",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "7725",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*4",
      "actual-mtu": "1500",
      "comment": "TO-R17C",
      "default-name": "ether3",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:14",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:EC:09:59",
      "mtu": "1500",
      "name": "ether3",
      "running": "true",
      "rx-byte": "574035",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "4697",
      "tx-byte": "768199",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "6827",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*5",
      "actual-mtu": "1500",
      "comment": "TO-R14C",
      "default-name": "ether4",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:14",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:C2:6A:3C",
      "mtu": "1500",
      "name": "ether4",
      "running": "true",
      "rx-byte": "526770",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "3983",
      "tx-byte": "719909",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "6113",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*6",
      "actual-mtu": "1500",
      "comment": "TO-R20M",
      "default-name": "ether5",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:14",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:7E:CB:06",
      "mtu": "1500",
      "name": "ether5",
      "running": "true",
      "rx-byte": "1081721",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "11016",
      "tx-byte": "949734",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "9080",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*1",
      "actual-mtu": "65536",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:04",
      "link-downs": "0",
      "mac-address": "00:00:00:00:00:00",
      "mtu": "65536",
      "name": "lo",
      "running": "true",
      "rx-byte": "0",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "0",
      "tx-byte": "0",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "0",
      "tx-queue-drop": "0",
      "type": "loopback"
    },
    {
      ".id": "*7",
      "actual-mtu": "1500",
      "comment": "Loopback1",
      "disabled": "false",
      "dynamic": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "l2mtu": "65535",
      "last-link-up-time": "2026-03-02 10:07:21",
      "link-downs": "0",
      "mac-address": "22:33:25:1D:9C:FF",
      "mtu": "auto",
      "name": "lo1",
      "running": "true",
      "rx-byte": "0",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "0",
      "tx-byte": "507285",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "2947",
      "tx-queue-drop": "0",
      "type": "bridge"
    }
  ]
}
```

### test_routing_ios (R5C — SSH)
```json
{
  "device": "R5C",
  "cli_style": "ios",
  "cache_hit": false,
  "parsed": {
    "entry": {
      "10.0.0.8/30": {
        "ip": "10.0.0.8",
        "mask": "30",
        "known_via": "eigrp 10",
        "distance": "170",
        "metric": "281856",
        "type": "routine ",
        "redist_via": "eigrp",
        "redist_via_tag": "10",
        "update": {
          "from": "192.168.10.5",
          "interface": "Ethernet0/1",
          "age": "04:05:48"
        },
        "paths": {
          "1": {
            "nexthop": "192.168.10.5",
            "from": "192.168.10.5",
            "age": "04:05:48",
            "interface": "Ethernet0/1",
            "prefer_non_rib_labels": false,
            "merge_labels": false,
            "metric": "281856",
            "share_count": "1"
          }
        }
      }
    },
    "total_prefixes": 1
  }
}
```

### test_ping_eos (R6A — eAPI)
```json
{
  "device": "R6A",
  "cli_style": "eos",
  "cache_hit": false,
  "parsed": [
    {
      "messages": [
        "PING 10.1.1.5 (10.1.1.5) 72(100) bytes of data.\n80 bytes from 10.1.1.5: icmp_seq=1 ttl=255 time=0.278 ms\n80 bytes from 10.1.1.5: icmp_seq=2 ttl=255 time=0.192 ms\n80 bytes from 10.1.1.5: icmp_seq=3 ttl=255 time=0.197 ms\n80 bytes from 10.1.1.5: icmp_seq=4 ttl=255 time=0.203 ms\n80 bytes from 10.1.1.5: icmp_seq=5 ttl=255 time=0.191 ms\n\n--- 10.1.1.5 ping statistics ---\n5 packets transmitted, 5 received, 0% packet loss, time 1ms\nrtt min/avg/max/mdev = 0.191/0.212/0.278/0.033 ms, ipg/ewma 0.273/0.244 ms\n"
      ]
    }
  ]
}
```

### test_routing_policies_ios (R8C — SSH)
```json
{
  "device": "R8C",
  "cli_style": "ios",
  "cache_hit": false,
  "raw": "route-map OSPF-TO-EIGRP, permit, sequence 10\n  Match clauses:\n  Set clauses:\n    metric 1000000 1 255 1 1500\n  Policy routing matches: 0 packets, 0 bytes\nroute-map ACCESS-R2-LO, permit, sequence 10\n  Match clauses:\n    ip address (access-lists): 100\n  Set clauses:\n    ip next-hop 10.1.1.6\n  Policy routing matches: 0 packets, 0 bytes"
}
```

### test_traceroute_ros (R20M — REST)
```json
{
  "device": "R20M",
  "cli_style": "routeros",
  "cache_hit": false,
  "parsed": [
    {
      ".section": "0",
      "address": "172.16.77.2",
      "avg": "0.5",
      "best": "0.5",
      "last": "0.5",
      "loss": "0",
      "sent": "1",
      "status": "",
      "std-dev": "0",
      "worst": "0.5"
    }
  ]
}
```

### test_run_show_eos (R7A — eAPI)
```json
{
  "device": "R7A",
  "cli_style": "eos",
  "cache_hit": false,
  "parsed": [
    {
      "ipV4Neighbors": [
        {
          "address": "10.1.1.10",
          "age": 9970,
          "hwAddress": "aabb.cc00.0d20",
          "interface": "Ethernet1"
        },
        {
          "address": "10.1.1.5",
          "age": 8246,
          "hwAddress": "aabb.cc00.1320",
          "interface": "Ethernet2"
        },
        {
          "address": "172.20.20.1",
          "age": 0,
          "hwAddress": "b637.a93a.176f",
          "interface": "Management0"
        }
      ],
      "totalEntries": 3,
      "staticEntries": 0,
      "dynamicEntries": 3,
      "notLearnedEntries": 0
    }
  ]
}
```

### test_redistribution_ros (R18M — REST)
```json
{
  "error": "Routing policy query 'redistribution' not supported on ROUTEROS",
  "device": "R18M"
}
```

## IT-003c: Cache Behavior

### test_cache_behavior (R3C — SSH)
```json
{
  "call_1_miss": {
    "device": "R3C",
    "cli_style": "ios",
    "cache_hit": true,
    "parsed": {
      "time": "16:15:26.092",
      "timezone": "UTC",
      "day_of_week": "Mon",
      "month": "Mar",
      "day": "2",
      "year": "2026"
    }
  },
  "call_2_hit": {
    "device": "R3C",
    "cli_style": "ios",
    "cache_hit": true,
    "parsed": {
      "time": "16:15:26.092",
      "timezone": "UTC",
      "day_of_week": "Mon",
      "month": "Mar",
      "day": "2",
      "year": "2026"
    }
  },
  "call_3_miss_after_ttl": {
    "device": "R3C",
    "cli_style": "ios",
    "cache_hit": false,
    "parsed": {
      "time": "16:15:32.382",
      "timezone": "UTC",
      "day_of_week": "Mon",
      "month": "Mar",
      "day": "2",
      "year": "2026"
    }
  }
}
```

## IT-003d: push_config (Loopback CRUD)

### test_push_config_ios (R3C)

#### Create
```json
{
  "R3C": {
    "transport_used": "asyncssh",
    "result": "interface Loopback99\nip address 10.99.99.1 255.255.255.255\nno shutdown\n"
  },
  "execution_time_seconds": 0.68,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R3C has critical role(s): ASBR, IGP_REDISTRIBUTOR, NAT_EDGE",
      "Change affects 6 SLA monitoring paths",
      "Interface disruption possible"
    ]
  },
  "rollback_advisory": [
    "no interface Loopback99",
    "no ip address 10.99.99.1 255.255.255.255",
    "shutdown"
  ]
}
```

#### Verify
```json
{
  "device": "R3C",
  "cli_style": "ios",
  "cache_hit": false,
  "parsed": {
    "interface": {
      "Ethernet0/0": {
        "ip_address": "172.20.20.203",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet0/1": {
        "ip_address": "192.168.10.5",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet0/2": {
        "ip_address": "192.168.10.1",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet0/3": {
        "ip_address": "10.0.0.6",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet1/0": {
        "ip_address": "10.0.0.10",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet1/1": {
        "ip_address": "200.50.50.5",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet1/2": {
        "ip_address": "200.40.40.5",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Ethernet1/3": {
        "ip_address": "unassigned",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "administratively down",
        "protocol": "down"
      },
      "Loopback1": {
        "ip_address": "3.3.3.3",
        "interface_is_ok": "YES",
        "method": "NVRAM",
        "status": "up",
        "protocol": "up"
      },
      "Loopback99": {
        "ip_address": "10.99.99.1",
        "interface_is_ok": "YES",
        "method": "manual",
        "status": "up",
        "protocol": "up"
      }
    }
  }
}
```

#### Delete
```json
{
  "R3C": {
    "transport_used": "asyncssh",
    "result": "no interface Loopback99\n"
  },
  "execution_time_seconds": 0.39,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R3C has critical role(s): ASBR, IGP_REDISTRIBUTOR, NAT_EDGE",
      "Change affects 6 SLA monitoring paths"
    ]
  },
  "rollback_advisory": [
    "interface Loopback99"
  ]
}
```

### test_push_config_eos (R1A)

#### Create
```json
{
  "R1A": {
    "transport_used": "eapi",
    "result": [
      {
        "output": ""
      },
      {
        "output": ""
      },
      {
        "output": ""
      },
      {
        "output": ""
      }
    ]
  },
  "execution_time_seconds": 0.02,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R1A has critical role(s): ABR",
      "Change affects 5 SLA monitoring paths"
    ]
  },
  "rollback_advisory": [
    "no interface Loopback99",
    "no ip address 10.99.99.1/32"
  ]
}
```

#### Verify
```json
{
  "device": "R1A",
  "cli_style": "eos",
  "cache_hit": false,
  "parsed": [
    {
      "interfaces": {
        "Ethernet1": {
          "name": "Ethernet1",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 1500,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "172.16.0.5",
              "maskLen": 30
            }
          },
          "nonRoutableClassEIntf": false
        },
        "Ethernet2": {
          "name": "Ethernet2",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 1500,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "172.16.0.9",
              "maskLen": 30
            }
          },
          "nonRoutableClassEIntf": false
        },
        "Ethernet3": {
          "name": "Ethernet3",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 1500,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "10.0.0.5",
              "maskLen": 30
            }
          },
          "nonRoutableClassEIntf": false
        },
        "Ethernet4": {
          "name": "Ethernet4",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 1500,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "10.0.0.1",
              "maskLen": 30
            }
          },
          "nonRoutableClassEIntf": false
        },
        "Loopback99": {
          "name": "Loopback99",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 65535,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "10.99.99.1",
              "maskLen": 32
            }
          },
          "nonRoutableClassEIntf": false
        },
        "Management0": {
          "name": "Management0",
          "interfaceStatus": "connected",
          "lineProtocolStatus": "up",
          "mtu": 1500,
          "ipv4Routable240": false,
          "ipv4Routable0": false,
          "interfaceAddress": {
            "ipAddr": {
              "address": "172.20.20.201",
              "maskLen": 24
            }
          },
          "nonRoutableClassEIntf": false
        }
      }
    }
  ]
}
```

#### Delete
```json
{
  "R1A": {
    "transport_used": "eapi",
    "result": [
      {
        "output": ""
      },
      {
        "output": ""
      },
      {
        "output": ""
      }
    ]
  },
  "execution_time_seconds": 0.02,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R1A has critical role(s): ABR",
      "Change affects 5 SLA monitoring paths"
    ]
  },
  "rollback_advisory": [
    "interface Loopback99"
  ]
}
```

### test_push_config_ros (R18M)

#### Create
```json
{
  "R18M": {
    "transport_used": "rest",
    "result": [
      {
        ".id": "*11",
        "actual-mtu": "1500",
        "ageing-time": "5m",
        "arp": "enabled",
        "arp-timeout": "auto",
        "auto-mac": "true",
        "comment": "Test loopback",
        "dhcp-snooping": "false",
        "disabled": "false",
        "dynamic": "false",
        "fast-forward": "true",
        "forward-delay": "15s",
        "igmp-snooping": "false",
        "l2mtu": "65535",
        "mac-address": "5A:CB:C6:87:04:DA",
        "max-learned-entries": "auto",
        "max-message-age": "20s",
        "mtu": "auto",
        "mvrp": "false",
        "name": "Loopback99",
        "port-cost-mode": "long",
        "priority": "0x8000",
        "protocol-mode": "rstp",
        "running": "true",
        "transmit-hold-count": "6",
        "vlan-filtering": "false"
      }
    ]
  },
  "execution_time_seconds": 0.01,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R18M has critical role(s): ASBR, NAT_EDGE",
      "Change affects 2 SLA monitoring path(s)"
    ]
  },
  "rollback_advisory": [
    "# RouterOS PUT rollback requires manual action: /rest/interface/bridge"
  ]
}
```

#### Verify
```json
{
  "device": "R18M",
  "cli_style": "routeros",
  "cache_hit": false,
  "parsed": [
    {
      ".id": "*2",
      "actual-mtu": "1500",
      "default-name": "ether1",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "0C:00:6B:6D:CE:00",
      "mtu": "1500",
      "name": "ether1",
      "running": "true",
      "rx-byte": "121529",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "1640",
      "tx-byte": "2941591",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "10732",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*3",
      "actual-mtu": "1500",
      "comment": "TO-R14C",
      "default-name": "ether2",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:0F:35:1A",
      "mtu": "1500",
      "name": "ether2",
      "running": "true",
      "rx-byte": "562718",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "4526",
      "tx-byte": "756370",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "6660",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*4",
      "actual-mtu": "1500",
      "comment": "TO-R17C",
      "default-name": "ether3",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:5B:8E:0D",
      "mtu": "1500",
      "name": "ether3",
      "running": "true",
      "rx-byte": "514043",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "3798",
      "tx-byte": "706974",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "5924",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*5",
      "actual-mtu": "1500",
      "comment": "TO-R19M",
      "default-name": "ether4",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:F8:4E:79",
      "mtu": "1500",
      "name": "ether4",
      "running": "true",
      "rx-byte": "874042",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "7730",
      "tx-byte": "744561",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "5817",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*6",
      "actual-mtu": "1500",
      "comment": "TO-R20M",
      "default-name": "ether5",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "AA:C1:AB:90:85:E9",
      "mtu": "1500",
      "name": "ether5",
      "running": "true",
      "rx-byte": "1055747",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "10651",
      "tx-byte": "1190609",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "12633",
      "tx-queue-drop": "0",
      "type": "ether"
    },
    {
      ".id": "*11",
      "actual-mtu": "1500",
      "comment": "Test loopback",
      "disabled": "false",
      "dynamic": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "l2mtu": "65535",
      "last-link-up-time": "2026-03-02 16:15:34",
      "link-downs": "0",
      "mac-address": "5A:CB:C6:87:04:DA",
      "mtu": "auto",
      "name": "Loopback99",
      "running": "true",
      "rx-byte": "0",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "0",
      "tx-byte": "0",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "0",
      "tx-queue-drop": "0",
      "type": "bridge"
    },
    {
      ".id": "*1",
      "actual-mtu": "65536",
      "disabled": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "last-link-up-time": "2026-03-02 10:07:06",
      "link-downs": "0",
      "mac-address": "00:00:00:00:00:00",
      "mtu": "65536",
      "name": "lo",
      "running": "true",
      "rx-byte": "0",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "0",
      "tx-byte": "0",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "0",
      "tx-queue-drop": "0",
      "type": "loopback"
    },
    {
      ".id": "*7",
      "actual-mtu": "1500",
      "comment": "Loopback1",
      "disabled": "false",
      "dynamic": "false",
      "fp-rx-byte": "0",
      "fp-rx-packet": "0",
      "fp-tx-byte": "0",
      "fp-tx-packet": "0",
      "l2mtu": "65535",
      "last-link-up-time": "2026-03-02 10:07:22",
      "link-downs": "0",
      "mac-address": "36:63:A7:C4:52:45",
      "mtu": "auto",
      "name": "lo1",
      "running": "true",
      "rx-byte": "0",
      "rx-drop": "0",
      "rx-error": "0",
      "rx-packet": "0",
      "tx-byte": "507104",
      "tx-drop": "0",
      "tx-error": "0",
      "tx-packet": "2944",
      "tx-queue-drop": "0",
      "type": "bridge"
    }
  ]
}
```

#### Delete
```json
{
  "R18M": {
    "transport_used": "rest",
    "result": [
      {
        "status": "deleted"
      }
    ]
  },
  "execution_time_seconds": 0.03,
  "risk_assessment": {
    "risk": "high",
    "devices": 1,
    "reasons": [
      "R18M has critical role(s): ASBR, NAT_EDGE",
      "Change affects 2 SLA monitoring path(s)"
    ]
  },
  "rollback_advisory": [
    "# RouterOS DELETE rollback requires manual action: /rest/interface/bridge/*11"
  ]
}
```
