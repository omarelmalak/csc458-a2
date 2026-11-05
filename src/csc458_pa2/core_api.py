from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .model import ControlMessage, Route


class CoreAPI(Protocol):
    def send_control(self, neighbor: str, message: ControlMessage) -> None: ...


class RoutingCore(ABC):
    """Protocol-only interface.

    Student code deliberately has no Mininet object, Linux shell, topology, or
    global graph. It sees only its own prefix, local link events, and control
    messages received from one-hop neighbors.
    """

    PERIOD_SECONDS = 2.0

    def __init__(self, router_id: str, own_prefix: str, api: CoreAPI):
        self.router_id = router_id
        self.own_prefix = own_prefix
        self._api = api

    def send_control(self, neighbor: str, message: ControlMessage) -> None:
        self._api.send_control(neighbor, message)

    @abstractmethod
    def on_link_change(self, neighbor: str, cost: int | None) -> None:
        """Local interface becomes usable/changes cost (int) or unusable (None)."""

    @abstractmethod
    def on_control(self, src: str, message: ControlMessage) -> None:
        """Process one control message from a directly connected neighbor."""

    @abstractmethod
    def on_periodic(self) -> None:
        """Called by the supplied daemon once per protocol refresh period."""

    @abstractmethod
    def get_route(self, prefix: str) -> Route | None:
        """Return current route to prefix, or None if unknown/unreachable."""

    @abstractmethod
    def all_routes(self) -> dict[str, Route]:
        """Return a copy of all usable remote routes, keyed by prefix."""

    @abstractmethod
    def debug_state(self) -> str:
        pass
