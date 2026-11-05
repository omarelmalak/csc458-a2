#!/usr/bin/env python3
"""Run a small batch of Mininet experiments and print a CSV-like summary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("topology", default="failure_alt.json", nargs="?")
    args = p.parse_args()
    print("protocol,mode,initial_s,event_s,messages,bytes")
    for protocol, mode in [("DV","basic"),("DV","poison_reverse"),("LS","")]:
        tag = f"batch_{protocol.lower()}_{mode or 'default'}"
        wd = ROOT / "run" / tag
        python = "/usr/bin/python3" if Path("/usr/bin/python3").exists() else sys.executable
        cmd = ["sudo", python, str(ROOT / "tools" / "run_mininet.py"), args.topology, "--protocol", protocol, "--workdir", str(wd)]
        if protocol == "DV": cmd += ["--dv-mode", mode]
        cp = subprocess.run(cmd)
        if cp.returncode != 0:
            continue
        data = json.loads((wd / "results.json").read_text())
        ev = data.get("events", [{}])[0].get("convergence_seconds", "") if data.get("events") else ""
        st = data.get("final_stats", {})
        print(f"{protocol},{mode},{data.get('initial_convergence_seconds','')},{ev},{st.get('messages_sent','')},{st.get('bytes_sent','')}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
