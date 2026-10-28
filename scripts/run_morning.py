#!/usr/bin/env python3
"""Pipeline: Helen context → Beef (never the goal) → compile Brief."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(script: str) -> None:
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)


def main() -> int:
    run("ingest_bio.py")
    run("extract_signals.py")
    run("update_beef.py")
    run("draft_brief.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
