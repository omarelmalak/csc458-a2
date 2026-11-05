import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.mininet
ROOT = Path(__file__).resolve().parents[1]


def test_mininet_dv_smoke():
    if os.geteuid() != 0 or shutil.which("mn") is None:
        pytest.skip("requires root and Mininet")
    cp = subprocess.run([sys.executable, str(ROOT / "tools" / "mininet_smoke.py"), "--protocol", "DV"], timeout=30)
    assert cp.returncode == 0
