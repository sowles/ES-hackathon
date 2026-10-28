#!/usr/bin/env python3
"""Refresh briefs/pending.md from Helen snapshots + last review.

This is the Chief Brief payload (plan.md). `/chief` still scores PRDs against
Current OKRs in plan.md until leadership Accepts. Never edits those OKRs.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ACTION_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}T\S+)\s+—\s+(accept|request-changes|decline)\b",
    re.I | re.M,
)
OKR_RE = re.compile(r"^(\d+)\.\s+(.+)$", re.M)

# Helen-backed lines inferred from her files (see docs/helen-okr-pack-h2-2026.md).
# Evidence ids must exist in the snapshot; drop a line if none of its ids remain.
HELEN_LINES = [
    {
        "line": "Close the CB-101 TSA (tech transfer, batch records, phase 2 clinical database, named contractors) by 31 Dec 2026.",
        "evidence": ["email-0024", "email-0010", "event-0002"],
        "okr_pack": "O1 KR1.1",
    },
    {
        "line": "Hold the CB-201 manufacturing slot at Harbor Biologics; miss it and phase 1 slips.",
        "evidence": ["email-0022", "email-0014", "email-0008"],
        "okr_pack": "O2 KR2.1",
    },
    {
        "line": "Put a CB-230 keep / partner / stop decision on the January 2027 board. Fund it only through the current fiscal year until then.",
        "evidence": ["email-0013", "email-0003", "event-0001"],
        "okr_pack": "O3 KR3.1",
    },
    {
        "line": "October / January board pack is decisions (TSA close, Harbor, CB-230, 2027 budget) — not a GSK recap.",
        "evidence": ["email-0019", "email-0002", "email-0016"],
        "okr_pack": "O4 KR4.3",
    },
]


def parse_okrs(plan_text: str) -> list[str]:
    chunk = plan_text.split("## Current OKRs", 1)[-1]
    chunk = chunk.split("## ", 1)[0]
    return [m.group(2).strip() for m in OKR_RE.finditer(chunk)]


def latest_review(review_text: str) -> dict:
    matches = list(ACTION_RE.finditer(review_text))
    if not matches:
        return {"action": "none", "at": None, "raw": ""}
    m = matches[-1]
    return {
        "action": m.group(2).lower(),
        "at": m.group(1),
        "raw": review_text[m.start() :].strip(),
    }


def declined_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for row in path.read_text(encoding="utf-8").splitlines():
        if not row.startswith("|") or "_none_" in row or row.startswith("| Declined"):
            continue
        if set(row.replace("|", "").strip()) <= set("- "):
            continue
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) >= 2 and cols[1]:
            out.append(cols[1])
    return out


def load_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for name in ("events.jsonl", "emails.jsonl"):
        path = root / "data" / "raw" / name
        if not path.exists():
            continue
        for line in path.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            ids.add(json.loads(line).get("id") or "")
    ids.discard("")
    return ids


def manifest_pulled_at(root: Path) -> str:
    path = root / "data" / "raw" / "manifest.json"
    if path.exists():
        return json.loads(path.read_text()).get("pulled_at") or "unknown"
    return "unknown"


def render(
    *,
    pulled_at: str,
    review: dict,
    published: list[str],
    proposed: list[dict],
    declined: list[str],
    comments: str,
) -> str:
    action = review["action"]
    lines = [
        "# Chief Brief",
        "",
        "Payload for the Chief Brief page in [plan.md](../plan.md). Morning ingest rewrites this file.",
        "`/chief` still reads **Current OKRs in plan.md** until Accept. This file is the proposed diff, blame, and decisions-needed view.",
        "",
        f"- Status: **open** (last review: `{action}`)",
        f"- Snapshot: `{pulled_at}`",
        "- `/chief` calls: **none recorded yet** (seed batch in plan.md still applies)",
        "",
        "## 1. Decisions needed",
        "",
        "At most three items blocked on the CEO or CPO. From Helen's files vs the published seed:",
        "",
        "1. Published OKRs are trial-site / months-of-supply / runway. Helen's mail and calendar are TSA close, Harbor slot, and CB-230 for the January board. Accept Helen's lines, or keep the seed?",
        "2. Harbor slot vs capital discipline is still open in her files (`email-0022`, `email-0014`). Hold the date, or wait on 2027 budget?",
        "3. CB-230 keep / partner / stop is due before the January board (`email-0013`, `event-0001`). Put it on the pack?",
        "",
        "## 2. Effort by OKR (say versus do)",
        "",
        "From the seed batch in plan.md until a `/chief` call log exists: OKR 1 has 3 (Nate beside, Jordan, Owen), OKR 2 has 1 (Alex), OKR 3 has 1 (Sam), beside or none has 1 (Nate's Primer3).",
        "",
        "## 3. What engineers are doing",
        "",
        "See seed batch in plan.md. Ingest does not invent `/chief` calls. Work beside an OKR is a **branch** (Nate / Primer3).",
        "",
        "## 4. Merge conflicts",
        "",
        "From plan.md: Jordan and Alex are both forecasting months of supply for the new site.",
        "",
        "## 5. Published plan (`plan.md` Current OKRs)",
        "",
    ]
    if published:
        for i, o in enumerate(published, 1):
            lines.append(f"{i}. {o}")
    else:
        lines.append("_none_")
    lines += [
        "",
        "## Proposed performance (from Helen’s mail and calendar)",
        "",
    ]
    if not proposed:
        lines.append("_Nothing new to propose (declined, or evidence ids missing)._")
    else:
        for i, item in enumerate(proposed, 1):
            ev = ", ".join(f"`{e}`" for e in item["evidence"])
            lines.append(f"{i}. {item['line']}")
            lines.append(f"   - Pack: {item['okr_pack']}. Evidence: {ev}")
    lines += [
        "",
        "## Priorities | Performance",
        "",
        "| Priorities (published) | Performance (Helen snapshot) |",
        "| --- | --- |",
    ]
    n = max(len(published), len(proposed))
    for i in range(n):
        left = published[i] if i < len(published) else "—"
        right = proposed[i]["line"] if i < len(proposed) else "—"
        lines.append(f"| {left} | {right} |")
    lines += [
        "",
        "## Blame",
        "",
        "Helen evidence ids are on each Performance line. Engineer PRD / `/chief` call blame is owned by the Brief UI once the call log exists.",
        "",
        "## History",
        "",
        "No accepted versions yet. After Accept, archive under `briefs/accepted/` with who accepted and when, so the brief can show how many times a line has moved.",
        "",
        "## If leadership Accepts",
        "",
        "Republish Current OKRs in `plan.md` from the Performance column. The next `/chief` uses that plan and opens with \"Plan changed since your last call.\"",
        "",
        "## Last review",
        "",
        f"Action: `{action}`" + (f" at `{review['at']}`" if review.get("at") else ""),
        "",
    ]
    if comments and action != "none":
        lines.append("```")
        lines.append(comments[:4000])
        lines.append("```")
        lines.append("")
    if declined:
        lines.append("## Declined (do not re-propose)")
        lines.append("")
        for d in declined:
            lines.append(f"- {d}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root: Path = args.root

    plan = (root / "plan.md").read_text(encoding="utf-8")
    review = latest_review((root / "briefs" / "REVIEW.md").read_text(encoding="utf-8"))
    declined = declined_lines(root / "briefs" / "declined.md")
    ids = load_ids(root)
    published = parse_okrs(plan)

    proposed = []
    for item in HELEN_LINES:
        if any(item["line"] == d or d in item["line"] for d in declined):
            continue
        present = [e for e in item["evidence"] if e in ids]
        if not present:
            continue
        proposed.append({**item, "evidence": present})

    if review["action"] == "request-changes":
        # Keep proposing, but the review block is quoted in the brief for /chief.
        pass

    text = render(
        pulled_at=manifest_pulled_at(root),
        review=review,
        published=published,
        proposed=proposed,
        declined=declined,
        comments=review.get("raw") or "",
    )
    out_dir = root / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pending.md").write_text(text, encoding="utf-8")
    print(f"wrote {out_dir / 'pending.md'} ({len(proposed)} proposed lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
