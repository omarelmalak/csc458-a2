#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from csc458_pa2.mininet_lab import MininetLab
from csc458_pa2.topology import Topology


def main() -> int:
    topo = Topology.load(ROOT / "topologies" / "mininet_intro.json")
    lab = MininetLab(topo, ROOT / "run" / "intro", protocol="DV")
    try:
        lab.build()
        from mininet.cli import CLI
        print("\nPA2 Mininet warm-up. No routing daemons are running.")
        print("Use 'nodes', 'net', '<node> ip addr', '<node> ip route', ping, traceroute,")
        print("and manually add the static routes requested in the handout.\n")
        CLI(lab.net)
        return 0
    finally:
        lab.stop()


if __name__ == "__main__":
    raise SystemExit(main())
