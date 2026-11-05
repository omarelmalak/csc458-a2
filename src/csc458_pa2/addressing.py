from __future__ import annotations

import ipaddress
import re


def router_number(router_id: str) -> int:
    m = re.fullmatch(r"R(\d+)", router_id.upper())
    if not m:
        raise ValueError(f"router IDs must look like R1, R2, ...; got {router_id!r}")
    n = int(m.group(1))
    if not 1 <= n <= 99:
        raise ValueError("router number must be in [1, 99]")
    return n


def node_name(router_id: str) -> str:
    return router_id.lower()


def host_name(router_id: str) -> str:
    return f"h{router_number(router_id)}"


def stub_prefix(router_id: str) -> str:
    n = router_number(router_id)
    return f"10.{n}.0.0/24"


def router_stub_ip(router_id: str) -> str:
    n = router_number(router_id)
    return f"10.{n}.0.1"


def host_ip(router_id: str) -> str:
    n = router_number(router_id)
    return f"10.{n}.0.2"


def link_index(a: str, b: str) -> int:
    x, y = sorted((router_number(a), router_number(b)))
    # Unique for router numbers <= 99, and comfortably inside 10.254.0.0/16.
    idx = (x - 1) * 100 + (y - 1)
    if idx > 16383:
        raise ValueError("too many/router IDs too large for address allocator")
    return idx


def link_network(a: str, b: str) -> ipaddress.IPv4Network:
    idx = link_index(a, b)
    base = int(ipaddress.IPv4Address("10.254.0.0")) + 4 * idx
    return ipaddress.IPv4Network((base, 30))


def endpoint_ip(a: str, b: str, endpoint: str) -> str:
    net = link_network(a, b)
    lo, hi = sorted((a, b), key=router_number)
    if endpoint == lo:
        return str(net.network_address + 1)
    if endpoint == hi:
        return str(net.network_address + 2)
    raise ValueError(f"{endpoint} is not endpoint of {a}-{b}")


def intf_name(local: str, peer: str) -> str:
    # E.g., r1-r2. Linux interface names must be <=15 chars.
    name = f"{node_name(local)}-{node_name(peer)}"
    if len(name) > 15:
        raise ValueError(f"interface name too long: {name}")
    return name


def stub_intf_name(router_id: str) -> str:
    name = f"{node_name(router_id)}-stub"
    if len(name) > 15:
        raise ValueError(f"interface name too long: {name}")
    return name
