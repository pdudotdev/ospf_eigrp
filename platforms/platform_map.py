PLATFORM_MAP = {
    "ios": {
        "ospf": {
            "neighbors": "show ip ospf neighbor",
            "database": "show ip ospf database",
            "borders": "show ip ospf border-routers",
            "config": "show running-config | section ospf",
            "interfaces": "show ip ospf interface",            
            "details": "show ip ospf"
        },
        "eigrp": {
            "neighbors": "show ip eigrp neighbors",
            "topology": "show ip eigrp topology",
            "config": "show running-config | section eigrp",
            "interfaces": "show ip eigrp interfaces detail"            
        },
        "bgp": {
            "summary": "show ip bgp summary",
            "table": "show ip bgp",
            "config": "show running-config | section bgp"
        },
        "routing_table": {
            "ip_route": "show ip route"
        },
        "routing_policies": {
            "redistribution": "show run | section redistribute",
            "route_maps": "show route-map",
            "prefix_lists": "show ip prefix-list",
            "policy_based_routing": "show ip policy",
            "access_lists": "show ip access-lists",
            "nat_pat": "show ip nat translation"
        },
        "interfaces": {
            "interface_status": "show ip interface brief"
        },
        "tools":{
            "ping": "ping",
            "traceroute": "traceroute"
        }
    },
    "eos": {
        "ospf": {
            "neighbors": "show ip ospf neighbor",
            "database": "show ip ospf database",
            "borders": "show ip ospf border-routers",
            "config": "show running-config | section ospf",
            "interfaces": "show ip ospf interface",            
            "details": "show ip ospf"
        },
        "bgp": {
            "summary": "show ip bgp summary",
            "table": "show ip bgp",
            "config": "show running-config | section bgp"
        },
        "routing_table": {
            "ip_route": "show ip route"
        },
        "routing_policies": {
            "redistribution": "show run | section redistribute",
            "route_maps": "show route-map",
            "prefix_lists": "show ip prefix-list",
            "access_lists": "show ip access-lists",
            "nat_pat": "show ip nat translation"
        },
        "interfaces": {
            "interface_status": "show ip interface brief"
        },
        "tools":{
            "ping": "ping",
            "traceroute": "traceroute"
        }
    },
    "routeros": {
        "ospf": {
            "neighbors": {"method": "GET", "path": "/rest/routing/ospf/neighbor"},
            "database": {"method": "GET", "path": "/rest/routing/ospf/lsa"},
            "interfaces": {"method": "GET", "path": "/rest/routing/ospf/interface"},
            "config": {"method": "GET", "path": "/rest/routing/ospf/instance"}
        },
        "bgp": {
            "summary": {"method": "GET", "path": "/rest/routing/bgp/connection"},
            "table": {"method": "GET", "path": "/rest/routing/route"},
            "config": {"method": "GET", "path": "/rest/routing/bgp/session"}
        },
        "routing_table": {
            "ip_route": {"method": "GET", "path": "/rest/ip/route"}
        },
        "routing_policies": {
            "prefix_lists": {"method": "GET", "path": "/rest/routing/filter/rule"},
            "route_maps": {"method": "GET", "path": "/rest/routing/filter/chain"},
            "access_lists": {"method": "GET", "path": "/rest/ip/firewall/filter"},
            "nat_pat": {"method": "GET", "path": "/rest/ip/firewall/nat"}
        },
        "interfaces": {
            "interface_status": {"method": "GET", "path": "/rest/interface"}
        },
        "tools": {
            "ping": {"method": "POST", "path": "/rest/tool/ping"},
            "traceroute": {"method": "POST", "path": "/rest/tool/traceroute", "default_body": {"count": 1, "max-hops": 15}}
        }
    }
}