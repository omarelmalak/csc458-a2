from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .addressing import stub_prefix
from .dv_core import DVCore
from .ls_core import LSCore
from .model import ControlMessage, Route
from .oracle import expected_prefix_routes
from .topology import Topology


class HarnessAPI:
    def __init__(self, harness: "CoreHarness", router_id: str):
        self.harness = harness
        self.router_id = router_id

    def send_control(self, neighbor: str, message: ControlMessage) -> None:
        self.harness.send(self.router_id, neighbor, message)


class CoreHarness:
    """Small deterministic unit-test harness, not the student experiment environment.

    The real assignment experiments run the same cores as UDP daemons inside
    Mininet. This harness exists so pytest can test protocol logic without root.
    """

    def __init__(self, topology: Topology, protocol: str, dv_mode: str = "poison_reverse"):
        self.topology = topology.clone()
        self.protocol = protocol.upper()
        self.dv_mode = dv_mode
        self.queue: deque[tuple[str, str, ControlMessage]] = deque()
        self.messages_sent = 0
        self.bytes_sent = 0
        self.cores = {}
        for rid in self.topology.routers:
            api = HarnessAPI(self, rid)
            if self.protocol == "DV":
                self.cores[rid] = DVCore(rid, stub_prefix(rid), api, dv_mode)
            else:
                self.cores[rid] = LSCore(rid, stub_prefix(rid), api)
        for link in self.topology.links.values():
            if link.active:
                self.cores[link.a].on_link_change(link.b, link.cost)
                self.cores[link.b].on_link_change(link.a, link.cost)

    def send(self, src: str, dst: str, msg: ControlMessage) -> None:
        try:
            link = self.topology.link(src, dst)
        except KeyError:
            return
        if link.active:
            self.queue.append((src, dst, msg))
            self.messages_sent += 1
            self.bytes_sent += msg.encoded_size()

    def step(self, periodic: bool = False) -> int:
        current = list(self.queue)
        self.queue.clear()
        for src, dst, msg in current:
            try:
                link = self.topology.link(src, dst)
            except KeyError:
                continue
            if link.active:
                self.cores[dst].on_control(src, msg)
        if periodic:
            for core in self.cores.values():
                core.on_periodic()
        return len(current)

    def converge(self, max_steps: int = 100) -> int:
        stable = 0
        for step in range(1, max_steps + 1):
            delivered = self.step(periodic=(step % 10 == 0))
            if self.all_optimal() and not self.queue:
                stable += 1
                if stable >= 2:
                    return step
            else:
                stable = 0
            if delivered == 0 and not self.queue and not self.all_optimal():
                # periodic refresh can sometimes be required after malformed manual tests
                for core in self.cores.values():
                    core.on_periodic()
        raise TimeoutError("protocol did not converge")

    def all_optimal(self) -> bool:
        for src in self.topology.routers:
            expected = expected_prefix_routes(self.topology, src)
            actual = self.cores[src].all_routes()
            if actual != expected:
                return False
        return True

    def link_down(self, a: str, b: str) -> None:
        link = self.topology.link(a, b)
        link.active = False
        self.cores[a].on_link_change(b, None)
        self.cores[b].on_link_change(a, None)

    def link_up(self, a: str, b: str, cost: int | None = None) -> None:
        link = self.topology.link(a, b)
        if cost is not None:
            link.cost = cost
        link.active = True
        self.cores[a].on_link_change(b, link.cost)
        self.cores[b].on_link_change(a, link.cost)

    def cost_change(self, a: str, b: str, cost: int) -> None:
        link = self.topology.link(a, b)
        link.cost = cost
        if link.active:
            self.cores[a].on_link_change(b, cost)
            self.cores[b].on_link_change(a, cost)


def load_harness(path: str | Path, protocol: str, dv_mode: str = "poison_reverse") -> CoreHarness:
    return CoreHarness(Topology.load(path), protocol, dv_mode)
