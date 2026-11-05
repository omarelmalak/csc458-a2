from __future__ import annotations

import subprocess
from typing import Callable

from .prefix_tools import canonical_prefix

from .model import INFINITY, Route


class LinuxRouteManager:
    """Staff-supplied adapter from protocol routes to the Linux FIB."""

    def __init__(self, neighbors: dict[str, dict], run: Callable[[list[str]], None] | None = None):
        self.neighbors = neighbors
        self._run = run or self._subprocess_run
        self.installed: dict[str, Route] = {}

    @staticmethod
    def _subprocess_run(argv: list[str]) -> None:
        subprocess.run(argv, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def sync(self, routes: dict[str, Route]) -> None:
        desired: dict[str, Route] = {}
        for prefix, route in routes.items():
            try:
                # PA1 owns CIDR canonicalization/LPM. PA2 reuses that implementation
                # instead of defining another prefix module.
                prefix = canonical_prefix(prefix)
            except (ValueError, TypeError):
                continue
            if route.metric >= INFINITY or route.next_hop is None or route.next_hop not in self.neighbors:
                continue
            desired[prefix] = route

        for prefix in sorted(set(self.installed) - set(desired)):
            self._run(["ip", "route", "del", prefix])
            self.installed.pop(prefix, None)

        for prefix, route in sorted(desired.items()):
            if self.installed.get(prefix) == route:
                continue
            n = self.neighbors[route.next_hop]
            self._run([
                "ip", "route", "replace", prefix, "via", n["peer_ip"],
                "dev", n["ifname"], "metric", str(route.metric), "proto", "static",
            ])
            self.installed[prefix] = route
