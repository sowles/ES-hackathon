#!/usr/bin/env python3
"""Accept / request-changes / decline. Accept is the only write to beef/goals.md."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from draft_brief import HELEN_LINES, compile_brief, parse_okrs

WINDOW_RE = re.compile(r"Window:\s+(.+?)\s+`(\d{4}-\d{2}-\d{2})`\s+…\s+`(\d{4}-\d{2}-\d{2})`")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def goal_windows(text: str) -> list[dict]:
    return [{"label": m.group(1).strip(), "start": m.group(2), "end": m.group(3)} for m in WINDOW_RE.finditer(text)]


def write_goals(root: Path, lines: list[str], windows: list[dict]) -> None:
    out = [
        "# Goal (Chief Beef)",
        "",
        "This is the only side of Beef that Accept may write. Pipelines never edit this file.",
        "",
    ]
    fallback = {"label": "accepted window", "start": "2026-06-01", "end": "2027-03-31"}
    for i, line in enumerate(lines):
        w = windows[i] if i < len(windows) else fallback
        out.append(f"{i + 1}. {line}")
        out.append(f"   - Window: {w['label']} (`{w['start']}` … `{w['end']}`)")
    (root / "beef" / "goals.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def append_review(root: Path, action: str, comment: str, brief_path: str) -> None:
    stamp = now_iso()
    block = [
        "",
        f"## {stamp} — {action}",
        "Reviewer: CEO / CPO (Chief Brief)",
        f"Brief: {brief_path}",
        "Notes:",
        f"- {comment.strip() or '(none)'}",
        "",
    ]
    path = root / "briefs" / "REVIEW.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n".join(block), encoding="utf-8")
    return stamp


def append_declined(root: Path, lines: list[str], reason: str) -> None:
    path = root / "briefs" / "declined.md"
    text = path.read_text(encoding="utf-8") if path.exists() else (
        "# Declined plan lines\n\n| Declined at | Line | Reason | Evidence ids at decline |\n| --- | --- | --- | --- |\n"
    )
    stamp = now_iso()
    extra = "".join(f"| {stamp} | {line} | {reason or 'declined'} | |\n" for line in lines)
    path.write_text(text.rstrip() + "\n" + extra, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--action", required=True, choices=("accept", "request-changes", "decline"))
    parser.add_argument("--comment", default="")
    args = parser.parse_args()
    root: Path = args.root

    pending = root / "briefs" / "pending.md"
    proposed = []
    data = compile_brief(root)
    proposed = list(data["proposed"])

    if args.action == "accept":
        goals_text = (root / "beef" / "goals.md").read_text(encoding="utf-8")
        windows = goal_windows(goals_text)
        if not proposed:
            proposed = parse_okrs(goals_text)
        write_goals(root, proposed, windows)
        accepted_dir = root / "briefs" / "accepted"
        accepted_dir.mkdir(parents=True, exist_ok=True)
        stamp = now_iso().replace(":", "")
        dest = accepted_dir / f"{stamp}.md"
        if pending.exists():
            dest.write_text(pending.read_text(encoding="utf-8"), encoding="utf-8")
        append_review(root, "accept", args.comment, str(dest.relative_to(root)))
    elif args.action == "decline":
        append_declined(root, proposed or [item["line"] for item in HELEN_LINES], args.comment)
        append_review(root, "decline", args.comment, "briefs/pending.md")
    else:
        append_review(root, "request-changes", args.comment, "briefs/pending.md")

    data = compile_brief(root)
    print(f"review {args.action}; goal lines={len(data['published'])} proposed={len(data['proposed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
