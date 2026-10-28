#!/usr/bin/env python3
"""Morning job: pull Helen → signals → refresh Chief Brief. Does not Accept."""

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
    run("draft_brief.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
