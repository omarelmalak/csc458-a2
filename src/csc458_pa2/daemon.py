from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import selectors
import socket
import time
from typing import Any

from .dv_core import DVCore
from .ls_core import LSCore
from .linux_routes import LinuxRouteManager
from .model import ControlMessage

CONTROL_PORT = 4582


class DaemonAPI:
    def __init__(self, sock: socket.socket, neighbors: dict[str, dict], stats: dict[str, int]):
        self.sock = sock
        self.neighbors = neighbors
        self.stats = stats

    def send_control(self, neighbor: str, message: ControlMessage) -> None:
        info = self.neighbors.get(neighbor)
        if not info or not info.get("active", False):
            return
        data = message.to_bytes()
        try:
            self.sock.sendto(data, (info["peer_ip"], CONTROL_PORT))
        except OSError:
            return
        self.stats["messages_sent"] += 1
        self.stats["bytes_sent"] += len(data)


def read_carrier(ifname: str) -> bool:
    try:
        return Path(f"/sys/class/net/{ifname}/carrier").read_text().strip() == "1"
    except OSError:
        return False


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True))
    os.replace(tmp, path)


def append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(f"{time.time():.6f} {text}\n")


class RoutingDaemon:
    def __init__(self, config: dict, protocol: str, dv_mode: str, status_path: Path, command_path: Path, log_path: Path):
        self.config = config
        self.router_id = config["router_id"]
        self.neighbors: dict[str, dict] = config["neighbors"]
        self.status_path = status_path
        self.command_path = command_path
        self.log_path = log_path
        self.command_offset = 0
        self.stats = {"messages_sent": 0, "bytes_sent": 0, "messages_received": 0, "bytes_received": 0}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", CONTROL_PORT))
        self.sock.setblocking(False)
        self.api = DaemonAPI(self.sock, self.neighbors, self.stats)
        if protocol == "DV":
            self.core = DVCore(self.router_id, config["own_prefix"], self.api, mode=dv_mode)
        elif protocol == "LS":
            self.core = LSCore(self.router_id, config["own_prefix"], self.api)
        else:
            raise ValueError("protocol must be DV or LS")
        self.protocol = protocol
        self.routes = LinuxRouteManager(self.neighbors)
        self.source_to_neighbor = {v["peer_ip"]: n for n, v in self.neighbors.items()}
        self.running = True
        self.next_periodic = time.monotonic() + self.core.PERIOD_SECONDS
        self.next_carrier_poll = 0.0
        self.carrier_state: dict[str, bool] = {}

    def _poll_carrier(self) -> None:
        for n, info in self.neighbors.items():
            up = read_carrier(info["ifname"])
            old = self.carrier_state.get(n)
            self.carrier_state[n] = up
            if old is None or old != up:
                info["active"] = up
                self.core.on_link_change(n, int(info["cost"]) if up else None)
                append_log(self.log_path, f"link {n} {'up' if up else 'down'} cost={info['cost']}")

    def _handle_control(self) -> None:
        try:
            data, (src_ip, _port) = self.sock.recvfrom(65535)
        except BlockingIOError:
            return
        src = self.source_to_neighbor.get(src_ip)
        if not src or not self.neighbors[src].get("active", False):
            return
        try:
            msg = ControlMessage.from_bytes(data)
        except Exception:
            return
        self.stats["messages_received"] += 1
        self.stats["bytes_received"] += len(data)
        self.core.on_control(src, msg)

    def _handle_commands(self) -> None:
        if not self.command_path.exists():
            return
        with self.command_path.open() as f:
            f.seek(self.command_offset)
            for line in f:
                try:
                    cmd = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = cmd.get("type")
                if kind == "cost_change":
                    n = str(cmd.get("neighbor"))
                    cost = int(cmd.get("cost"))
                    if n in self.neighbors and 1 <= cost < 16:
                        self.neighbors[n]["cost"] = cost
                        if self.carrier_state.get(n, False):
                            self.core.on_link_change(n, cost)
                        append_log(self.log_path, f"cost {n} -> {cost}")
                elif kind == "inject_control":
                    src = str(cmd.get("src"))
                    try:
                        msg = ControlMessage(str(cmd["protocol"]), dict(cmd["payload"]))
                    except Exception:
                        continue
                    self.core.on_control(src, msg)
                elif kind == "stop":
                    self.running = False
            self.command_offset = f.tell()

    def _write_status(self) -> None:
        routes = {p: {"metric": r.metric, "next_hop": r.next_hop} for p, r in self.core.all_routes().items()}
        atomic_json(self.status_path, {
            "router_id": self.router_id,
            "protocol": self.protocol,
            "own_prefix": self.config["own_prefix"],
            "neighbors": {n: {"cost": x["cost"], "active": bool(x.get("active"))} for n, x in self.neighbors.items()},
            "routes": routes,
            "stats": dict(self.stats),
            "debug": self.core.debug_state(),
            "time": time.time(),
        })

    def run(self) -> int:
        append_log(self.log_path, f"starting {self.protocol} daemon")
        sel = selectors.DefaultSelector()
        sel.register(self.sock, selectors.EVENT_READ)
        while self.running:
            now = time.monotonic()
            if now >= self.next_carrier_poll:
                self._poll_carrier()
                self.next_carrier_poll = now + 0.15
            self._handle_commands()
            if now >= self.next_periodic:
                self.core.on_periodic()
                self.next_periodic = now + self.core.PERIOD_SECONDS
            for _key, _mask in sel.select(timeout=0.05):
                self._handle_control()
            self.routes.sync(self.core.all_routes())
            self._write_status()
        append_log(self.log_path, "stopping")
        return 0


def main() -> int:
    p = argparse.ArgumentParser(description="CSC458 PA2 routing daemon (staff infrastructure)")
    p.add_argument("--config", required=True)
    p.add_argument("--protocol", choices=["DV", "LS"], required=True)
    p.add_argument("--dv-mode", choices=["basic", "split_horizon", "poison_reverse"], default="poison_reverse")
    p.add_argument("--status", required=True)
    p.add_argument("--commands", required=True)
    p.add_argument("--log", required=True)
    args = p.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    return RoutingDaemon(cfg, args.protocol, args.dv_mode, Path(args.status), Path(args.commands), Path(args.log)).run()


if __name__ == "__main__":
    raise SystemExit(main())
