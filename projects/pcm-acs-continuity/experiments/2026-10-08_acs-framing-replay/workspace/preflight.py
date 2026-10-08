"""Read-only ACS adapter; consult the pinned PCM/ACS code installed by the launcher."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
adapter = os.environ.get("ACS_PREFLIGHT_SCRIPT")
if not adapter or not Path(adapter).is_file():
    print("UNKNOWN: launch using tools/launch_acs_replay.py; ACS adapter unavailable", file=sys.stderr)
    raise SystemExit(3)
cmd = [sys.executable, adapter, "--expect", str(HERE / "decision-precondition.json"),
       "--task", "LAB-0001", "--repo", "Pukujan/test-repo"]
raise SystemExit(subprocess.run(cmd, cwd=HERE, check=False).returncode)
