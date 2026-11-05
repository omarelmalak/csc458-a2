#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    try:
        from csc458_pa2.prefix_tools import (
            canonical_prefix, prefix_contains, prefix_length, longest_prefix_match,
        )
        assert canonical_prefix("192.0.2.99/24") == "192.0.2.0/24"
        assert prefix_contains("10.0.0.0/8", "10.4.5.6")
        assert prefix_length("10.4.0.0/16") == 16
        assert longest_prefix_match(
            ["10.0.0.0/8", "10.4.0.0/16", "10.4.32.0/20"], "10.4.35.7"
        ) == "10.4.32.0/20"
    except Exception as exc:
        print("PA1 prefix-tools carry-forward: NOT READY")
        print("Run: python3 tools/import_pa1.py /path/to/your/PA1/repository")
        print(f"Reason: {exc}")
        return 1
    print("PA1 prefix-tools carry-forward: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
