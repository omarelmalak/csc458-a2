from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

INFINITY = 16


@dataclass(frozen=True)
class Route:
    """Route to an advertised IP prefix.

    metric is the IGP path cost. next_hop is a directly connected router ID.
    A metric >= INFINITY is considered unreachable.
    """

    metric: int
    next_hop: str | None


@dataclass(frozen=True)
class ControlMessage:
    protocol: str
    payload: dict[str, Any]

    def to_bytes(self) -> bytes:
        obj = {"protocol": self.protocol, "payload": self.payload}
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "ControlMessage":
        obj = json.loads(data.decode("utf-8"))
        if not isinstance(obj, dict) or not isinstance(obj.get("protocol"), str) or not isinstance(obj.get("payload"), dict):
            raise ValueError("invalid control message")
        return cls(obj["protocol"], obj["payload"])

    def encoded_size(self) -> int:
        return len(self.to_bytes())
