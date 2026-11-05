from __future__ import annotations

import heapq

from .addressing import stub_prefix
from .model import Route
from .topology import Topology


def active_neighbors(topo: Topology, router: str) -> dict[str, int]:
    out = {}
    for link in topo.links.values():
        if link.active and router in (link.a, link.b):
            out[link.other(router)] = link.cost
    return out


def shortest_router_route(topo: Topology, src: str, dst: str) -> Route | None:
    if src == dst:
        return Route(0, None)
    heap: list[tuple[int, str, tuple[str, ...], str]] = []
    for n, cost in active_neighbors(topo, src).items():
        heapq.heappush(heap, (cost, n, (src, n), n))
    best: dict[str, tuple[int, str, tuple[str, ...]]] = {}
    while heap:
        dist, first, path, node = heapq.heappop(heap)
        key = (dist, first, path)
        if node in best and best[node] <= key:
            continue
        best[node] = key
        if node == dst:
            return Route(dist, first)
        for n, cost in active_neighbors(topo, node).items():
            if n in path:
                continue
            heapq.heappush(heap, (dist + cost, first, path + (n,), n))
    return None


def expected_prefix_routes(topo: Topology, src: str) -> dict[str, Route]:
    out = {}
    for dst in topo.routers:
        if dst == src:
            continue
        r = shortest_router_route(topo, src, dst)
        if r is not None:
            out[stub_prefix(dst)] = r
    return out
