#!/usr/bin/env python3
"""Update Chief Beef *context* from Helen inflow. Never writes the goal.

Goal lives in beef/goals.md. Only an Accept may change it.
Unmatched inflow stays unclassified.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

OKR_RE = re.compile(r"^(\d+)\.\s+(.+)$", re.M)

# Goal windows from the current seed OKRs in plan.md.
OKR_WINDOWS = {
    "1": {"start": "2026-11-01", "end": "2027-03-31", "label": "site Nov / patients through Q1"},
    "2": {"start": "2026-06-01", "end": "2027-03-31", "label": "months of supply ≥ 3"},
    "3": {"start": "2026-06-01", "end": "2027-03-31", "label": "runway ≥ 12 months"},
}


def parse_okrs_from_goals(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip()) for m in OKR_RE.finditer(text)]


def seed_goals_if_missing(root: Path) -> None:
    path = root / "beef" / "goals.md"
    if path.exists():
        return
    plan = (root / "plan.md").read_text(encoding="utf-8")
    chunk = plan.split("## Current OKRs", 1)[-1].split("## ", 1)[0]
    okrs = [(m.group(1), m.group(2).strip()) for m in OKR_RE.finditer(chunk)]
    lines = [
        "# Goal (Chief Beef)",
        "",
        "This is the only side of Beef that Accept may write. Pipelines never edit this file.",
        "",
    ]
    for num, text in okrs:
        w = OKR_WINDOWS.get(num, {})
        lines.append(f"{num}. {text}")
        lines.append(
            f"   - Window: {w.get('label', '?')} (`{w.get('start', '')}` … `{w.get('end', '')}`)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def classify(text: str) -> tuple[str | None, str]:
    t = (text or "").lower()
    # Seed OKRs are trial site / MOS / runway. Helen's files are mostly TSA / Harbor / CB-230.
    # Only couple when the language is actually about those goals.
    if re.search(r"\b(runway|burn rate)\b", t) and not re.search(r"\b(primer|trial site)\b", t):
        relation = "fights" if re.search(r"\b(11 months|miss|below 12)\b", t) else "supports"
        return "3", relation
    if re.search(r"\bmonths of supply\b", t) or re.search(r"\bcold chain\b", t):
        return "2", "supports"
    if re.search(r"\b(trial site|new site|treated patients)\b", t):
        return "1", "supports"
    if re.search(r"\benrollment\b", t) and re.search(r"\b(site|trial|patient)\b", t):
        return "1", "beside"
    return None, "unclassified"


def in_window(when: str, okr: str | None) -> bool:
    if not okr or not when:
        return False
    day = when[:10]
    w = OKR_WINDOWS.get(okr)
    if not w:
        return False
    return w["start"] <= day <= w["end"]


def person_event(event: dict) -> str:
    for a in event.get("attendees") or []:
        name = a.get("name") or ""
        if name and "Helen" not in name:
            return name
    return "Helen Williamson"


def person_mail(mail: dict) -> str:
    folder = mail.get("folder")
    if folder == "sent":
        to = mail.get("to") or []
        if to:
            return to[0].get("name") or "unknown"
        return "Helen Williamson"
    return (mail.get("from") or {}).get("name") or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root: Path = args.root

    seed_goals_if_missing(root)
    goals_text = (root / "beef" / "goals.md").read_text(encoding="utf-8")
    okrs = parse_okrs_from_goals(goals_text)
    events = load_jsonl(root / "data" / "raw" / "events.jsonl")
    emails = load_jsonl(root / "data" / "raw" / "emails.jsonl")
    inflow: list[dict] = []

    for event in events:
        blob = " ".join(
            [
                event.get("title") or "",
                event.get("notes") or "",
                event.get("summary") or "",
            ]
        )
        okr, relation = classify(blob)
        if re.search(r"schedule review with nate", event.get("title") or "", re.I):
            okr, relation = None, "unclassified"
        when = (event.get("start") or event.get("date") or "")[:19]
        if okr and not in_window(when, okr):
            relation = "unclassified"
            okr = None
        inflow.append(
            {
                "id": event.get("id"),
                "source": "calendar",
                "person": person_event(event),
                "time": when,
                "title": event.get("title"),
                "okr": okr,
                "relation": relation,
                "window": OKR_WINDOWS[okr]["label"] if okr else None,
            }
        )

    for mail in emails:
        blob = " ".join([mail.get("subject") or "", mail.get("body") or ""])
        okr, relation = classify(blob)
        when = mail.get("sent_at") or ""
        if okr and not in_window(when, okr):
            relation = "unclassified"
            okr = None
        inflow.append(
            {
                "id": mail.get("id"),
                "source": "email",
                "person": person_mail(mail),
                "time": when[:19],
                "title": mail.get("subject"),
                "okr": okr,
                "relation": relation,
                "window": OKR_WINDOWS[okr]["label"] if okr else None,
            }
        )

    out_dir = root / "beef"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "inflow.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for row in inflow:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = Counter((r["okr"], r["relation"]) for r in inflow)
    coupled = [r for r in inflow if r["relation"] != "unclassified"]
    sent_unclass = [
        r
        for r in inflow
        if r["source"] == "email" and r["id"] and str(r["id"]).startswith("email-")
        and r["relation"] == "unclassified"
    ][:15]

    lines = [
        "# Chief Beef",
        "",
        "Context plus goal. Pipelines update **context** only. Accept is the only write to the goal (`beef/goals.md`).",
        "The Chief Brief (`briefs/pending.md`) is compiled from this file. Unclassified means no OKR match was forced.",
        "",
        "## The goal (do not pipeline-edit)",
        "",
    ]
    for num, text in okrs:
        w = OKR_WINDOWS.get(num, {})
        lines.append(f"{num}. {text}")
        lines.append(f"   - Window: {w.get('label', '?')} (`{w.get('start')}` … `{w.get('end')}`)")
    lines += [
        "",
        "## The context (Helen snapshot)",
        "",
        f"- Calendar events: {len(events)}",
        f"- Emails: {len(emails)}",
        f"- Coupled to an OKR: **{len(coupled)}**",
        f"- Unclassified: **{sum(1 for r in inflow if r['relation'] == 'unclassified')}**",
        "",
        "### Coupling counts (okr, relation)",
        "",
    ]
    for (okr, rel), n in sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        lines.append(f"- OKR {okr or 'none'} / {rel}: {n}")
    lines += [
        "",
        "## Coupled pairs (what arrived → OKR window)",
        "",
    ]
    if not coupled:
        lines.append("_No Helen item matched the seed OKRs with confidence._")
    else:
        for r in coupled[:40]:
            lines.append(
                f"- `{r['time']}` `{r['id']}` {r['person']}: **{r['title']}** → OKR {r['okr']} ({r['relation']}, {r['window']})"
            )
        if len(coupled) > 40:
            lines.append(f"- _+{len(coupled) - 40} more in inflow.jsonl_")
    lines += [
        "",
        "## Unclassified Helen sent mail (high signal, no seed-OKR match)",
        "",
        "These are TSA / Harbor / CB-230 threads. They stay unclassified against the current trial-site seed OKRs.",
        "",
    ]
    for r in sent_unclass:
        lines.append(f"- `{r['time']}` `{r['id']}` → **{r['title']}** ({r['person']})")
    lines.append("")
    (out_dir / "CHIEF_BEEF.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {jsonl} ({len(inflow)} rows) and CHIEF_BEEF.md ({len(coupled)} coupled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
