#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument("status_dir"); p.add_argument("router", nargs="?"); a=p.parse_args()
d=Path(a.status_dir)
files=[d/f"{a.router.upper()}.json"] if a.router else sorted(d.glob("R*.json"))
for f in files:
    print(f"== {f.name} ==")
    print(json.dumps(json.loads(f.read_text()), indent=2, sort_keys=True))
