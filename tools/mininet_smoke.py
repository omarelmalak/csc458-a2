#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from csc458_pa2.mininet_lab import MininetLab
from csc458_pa2.topology import Topology


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--protocol", choices=["DV", "LS"], default="DV")
    p.add_argument("--dv-mode", choices=["basic", "split_horizon", "poison_reverse"], default="poison_reverse")
    args = p.parse_args()
    topo = Topology.load(ROOT / "topologies" / "line4.json")
    lab = MininetLab(topo, ROOT / "run" / "smoke", args.protocol, args.dv_mode)
    try:
        lab.build(); lab.start_daemons()
        t = lab.wait_for_convergence(timeout=10)
        print("convergence_seconds:", t)
        print(lab.ping("R1", "R4", count=1))
        return 0 if t is not None else 2
    finally:
        lab.stop()


if __name__ == "__main__":
    raise SystemExit(main())
