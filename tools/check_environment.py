#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ok = True
    print(f"Python: {sys.version.split()[0]}")
    try:
        import mininet  # noqa: F401
        print("Mininet Python module: OK")
    except Exception as e:
        print(f"Mininet Python module: MISSING ({e})")
        ok = False

    required = ("mn", "ip", "ping", "traceroute", "tcpdump", "iperf3", "ovs-vsctl")
    optional = ("controller",)
    for exe in required + optional:
        path = shutil.which(exe)
        label = path or ("MISSING (optional for Part 0 Stage 7)" if exe in optional else "MISSING")
        print(f"{exe:12s}: {label}")
        if exe in required and not path:
            ok = False

    if os.geteuid() != 0:
        print("Note: Mininet experiments must be launched with sudo; unit tests do not require root.")

    if shutil.which("mn"):
        cp = subprocess.run(["mn", "--version"], text=True, capture_output=True)
        if cp.stdout.strip() or cp.stderr.strip():
            print("Mininet version:", (cp.stdout or cp.stderr).strip())

    try:
        from csc458_pa2.prefix_tools import canonical_prefix, longest_prefix_match
        assert canonical_prefix("192.0.2.99/24") == "192.0.2.0/24"
        assert longest_prefix_match(
            ["10.0.0.0/8", "10.4.0.0/16", "10.4.32.0/20"], "10.4.35.7"
        ) == "10.4.32.0/20"
        print("PA1 prefix_tools carry-forward: OK")
    except Exception as e:
        print(f"PA1 prefix_tools carry-forward: NOT READY ({e})")
        print("  Run: python3 tools/import_pa1.py /path/to/your/PA1/repository")
        ok = False

    print("Environment:", "READY" if ok else "INCOMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
