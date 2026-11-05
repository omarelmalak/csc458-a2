#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from csc458_pa2.mininet_lab import MininetLab
from csc458_pa2.routing_cli import make_routing_cli
from csc458_pa2.topology import Topology


def apply_event(lab: MininetLab, event: dict) -> str:
    kind = event["type"]
    a, b = event.get("a"), event.get("b")
    if kind == "link_down":
        lab.set_link(a, b, False); return f"link {a}-{b} DOWN"
    if kind == "link_up":
        if "cost" in event:
            lab.set_cost(a, b, int(event["cost"]))
        lab.set_link(a, b, True); return f"link {a}-{b} UP cost={lab.topology.link(a,b).cost}"
    if kind == "link_cost":
        lab.set_cost(a, b, int(event["cost"])); return f"cost {a}-{b} -> {event['cost']}"
    raise ValueError(f"unsupported event type: {kind}")


def main() -> int:
    p = argparse.ArgumentParser(description="Run CSC458 PA2 in Mininet")
    p.add_argument("topology")
    p.add_argument("--protocol", choices=["DV", "LS"], required=True)
    p.add_argument("--dv-mode", choices=["basic", "split_horizon", "poison_reverse"], default="poison_reverse")
    p.add_argument("--interactive", action="store_true", help="enter a custom Mininet CLI after initial convergence")
    p.add_argument("--capture", action="store_true", help="write one control-plane PCAP per router")
    p.add_argument("--no-events", action="store_true")
    p.add_argument("--workdir", default=None)
    args = p.parse_args()

    topo_path = Path(args.topology)
    if not topo_path.exists():
        topo_path = ROOT / "topologies" / args.topology
    topo = Topology.load(topo_path)
    workdir = Path(args.workdir) if args.workdir else ROOT / "run" / (topo_path.stem + "_" + args.protocol.lower())
    lab = MininetLab(topo, workdir, args.protocol, args.dv_mode, capture=args.capture)
    results = {"topology": topo.name, "protocol": args.protocol, "dv_mode": args.dv_mode, "events": []}
    try:
        lab.build(); lab.start_daemons()
        t0 = lab.wait_for_convergence()
        results["initial_convergence_seconds"] = t0
        results["initial_stats"] = lab.aggregate_stats()
        print(f"Initial convergence: {t0 if t0 is not None else 'TIMEOUT'}")
        if t0 is not None and len(topo.routers) >= 2:
            print(lab.ping(topo.routers[0], topo.routers[-1], count=1), end="")
        if args.interactive:
            print("Custom commands: routes R1 | status R1 | cost R1 R2 5 | converged")
            print("Standard Mininet link commands also work: link r1 r2 down/up")
            CLI = make_routing_cli(lab)
            CLI(lab.net)
        elif not args.no_events:
            for event in topo.events:
                time.sleep(float(event.get("after", 2.0)))
                before = lab.aggregate_stats()
                desc = apply_event(lab, event)
                print("EVENT:", desc)
                delay = lab.wait_for_convergence()
                elapsed = delay
                after = lab.aggregate_stats()
                rec = {"event": event, "convergence_seconds": elapsed, "stats_delta": {k: after[k]-before[k] for k in after}}
                results["events"].append(rec)
                print("Reconvergence:", elapsed if elapsed is not None else "TIMEOUT")
        results["final_stats"] = lab.aggregate_stats()
        (workdir / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
        print("Results:", workdir / "results.json")
        if args.capture:
            print("PCAPs:", workdir / "captures")
        return 0
    finally:
        lab.stop()


if __name__ == "__main__":
    raise SystemExit(main())
