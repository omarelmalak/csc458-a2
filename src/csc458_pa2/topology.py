from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .addressing import stub_prefix


@dataclass
class Link:
    a: str
    b: str
    cost: int
    active: bool = True
    delay_ms: float = 1.0

    def key(self) -> tuple[str, str]:
        return tuple(sorted((self.a, self.b)))  # type: ignore[return-value]

    def other(self, node: str) -> str:
        if node == self.a:
            return self.b
        if node == self.b:
            return self.a
        raise KeyError(node)


@dataclass
class Topology:
    name: str
    routers: list[str]
    links: dict[tuple[str, str], Link]
    events: list[dict[str, Any]] = field(default_factory=list)
    convergence_timeout: float = 12.0

    @classmethod
    def load(cls, path: str | Path) -> "Topology":
        data = json.loads(Path(path).read_text())
        routers = [str(x).upper() for x in data["routers"]]
        if len(set(routers)) != len(routers):
            raise ValueError("duplicate router IDs")
        for r in routers:
            stub_prefix(r)  # validates naming/range
        links: dict[tuple[str, str], Link] = {}
        for item in data["links"]:
            a, b = str(item["a"]).upper(), str(item["b"]).upper()
            if a not in routers or b not in routers or a == b:
                raise ValueError("invalid link endpoint")
            cost = int(item["cost"])
            if not 1 <= cost < 16:
                raise ValueError("link costs must be integers in [1, 15]")
            link = Link(a, b, cost, bool(item.get("active", True)), float(item.get("delay_ms", 1.0)))
            if link.key() in links:
                raise ValueError(f"duplicate link {a}-{b}")
            links[link.key()] = link
        events = list(data.get("events", []))
        for event in events:
            event.setdefault("after", 2.0)
        return cls(
            name=data.get("name", Path(path).stem),
            routers=routers,
            links=links,
            events=events,
            convergence_timeout=float(data.get("convergence_timeout", 12.0)),
        )

    def clone(self) -> "Topology":
        return Topology(
            self.name, list(self.routers),
            {k: Link(v.a, v.b, v.cost, v.active, v.delay_ms) for k, v in self.links.items()},
            [dict(e) for e in self.events], self.convergence_timeout,
        )

    def link(self, a: str, b: str) -> Link:
        key = tuple(sorted((a.upper(), b.upper())))
        return self.links[key]
