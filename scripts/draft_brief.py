#!/usr/bin/env python3
"""Compile briefs/pending.md and public/brief.json from Chief Beef. Never writes the goal."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ACTION_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}T\S+)\s+—\s+(accept|request-changes|decline)\b",
    re.I | re.M,
)
OKR_RE = re.compile(r"^(\d+)\.\s+(.+)$", re.M)
HISTORY_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}T\S+)\s+—\s+(accept|request-changes|decline)\b",
    re.I | re.M,
)

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
    if "## Current OKRs" in plan_text:
        chunk = plan_text.split("## Current OKRs", 1)[-1].split("## ", 1)[0]
    else:
        chunk = plan_text
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


def review_history(review_text: str) -> list[str]:
    out = []
    for m in HISTORY_RE.finditer(review_text):
        out.append(f"{m.group(1)} · {m.group(2).lower()}")
    return out[-8:]


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


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def manifest_pulled_at(root: Path) -> str:
    path = root / "data" / "raw" / "manifest.json"
    if path.exists():
        return json.loads(path.read_text()).get("pulled_at") or "unknown"
    return "unknown"


def display_date(pulled_at: str) -> str:
    try:
        dt = datetime.fromisoformat(pulled_at.replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y")
    except ValueError:
        return pulled_at[:10]


def short_okr(num: str, text: str) -> str:
    head = text.split(".")[0]
    if len(head) > 42:
        head = head[:40] + "…"
    return f"OKR {num} · {head}"


def by_id(inflow: list[dict]) -> dict[str, dict]:
    return {str(r.get("id")): r for r in inflow if r.get("id")}


def effort_bars(published: list[str], inflow: list[dict]) -> list[dict]:
    coupled = Counter(str(r["okr"]) for r in inflow if r.get("relation") != "unclassified" and r.get("okr"))
    unclass = sum(1 for r in inflow if r.get("relation") == "unclassified")
    bars = []
    for i, text in enumerate(published, 1):
        bars.append({"name": short_okr(str(i), text), "count": coupled.get(str(i), 0), "okr": str(i)})
    bars.append({"name": "Unclassified · no OKR match", "count": unclass, "okr": "none"})
    return bars


def people_from_inflow(inflow: list[dict], limit: int = 8) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in inflow:
        name = (row.get("person") or "").strip()
        if not name or name == "Helen Williamson":
            continue
        groups[name].append(row)
    people = []
    for name, rows in groups.items():
        rows.sort(key=lambda r: r.get("time") or "", reverse=True)
        coupled_rows = [r for r in rows if r.get("relation") != "unclassified"]
        use = coupled_rows or rows
        rels = Counter(r.get("relation") or "unclassified" for r in use)
        relation, _ = rels.most_common(1)[0]
        okr = next((r.get("okr") for r in use if r.get("okr")), None)
        if relation == "unclassified":
            tag = "unclassified"
        elif relation == "beside":
            tag = f"branch · OKR {okr}"
        else:
            tag = f"OKR {okr} · {relation}"
        latest = use[0]
        people.append(
            {
                "name": name,
                "work": latest.get("title") or "",
                "tag": tag,
                "count": len(rows),
                "coupled": len(coupled_rows),
                "latest": latest.get("time") or "",
            }
        )
    people.sort(key=lambda p: (-p["coupled"], -p["count"]))
    slim = [{k: p[k] for k in ("name", "work", "tag", "count")} for p in people]
    coupled = [p for p in slim if "unclassified" not in p["tag"]][: max(1, limit // 2)]
    other = [p for p in slim if "unclassified" in p["tag"]][: max(1, limit - len(coupled))]
    return coupled + other


def blame_for(ids: list[str], index: dict[str, dict]) -> list[str]:
    lines = []
    for eid in ids:
        row = index.get(eid)
        if not row:
            lines.append(eid)
            continue
        lines.append(
            f"{eid} · {row.get('person') or '?'} · {row.get('time') or ''} · {row.get('title') or ''}"
        )
    return lines


def diff_rows(published: list[str], proposed: list[dict], index: dict[str, dict]) -> list[dict]:
    n = max(len(published), len(proposed))
    rows = []
    for i in range(n):
        left_text = published[i] if i < len(published) else None
        right_item = proposed[i] if i < len(proposed) else None
        right_text = right_item["line"] if right_item else None
        if left_text and right_text and left_text == right_text:
            rows.append(
                {
                    "left": {"kind": "same", "text": left_text, "note": "goal"},
                    "right": {"kind": "same", "text": right_text, "note": "goal"},
                    "blame": [],
                }
            )
            continue
        left = None
        right = None
        if left_text:
            left = {"kind": "del", "text": left_text, "note": "beef/goals.md"}
        if right_text and right_item:
            ev = ", ".join(right_item["evidence"])
            right = {"kind": "add", "text": right_text, "note": ev}
        rows.append(
            {
                "left": left,
                "right": right,
                "blame": blame_for(right_item["evidence"], index) if right_item else [],
            }
        )
    return rows


def decisions(published: list[str], proposed: list[dict], inflow: list[dict]) -> list[str]:
    out = []
    seedish = any("trial site" in o.lower() or "runway" in o.lower() for o in published)
    helenish = any("TSA" in p["line"] or "Harbor" in p["line"] or "CB-230" in p["line"] for p in proposed)
    if seedish and helenish:
        out.append(
            "Published goal is trial-site / months of supply / runway. Helen's mail and calendar are TSA close, Harbor slot, and CB-230. Accept her lines into the goal, or keep the seed?"
        )
    if any("Harbor" in p["line"] for p in proposed):
        out.append("Harbor slot vs capital discipline is still in her files. Hold the date, or wait on 2027 budget?")
    if any("CB-230" in p["line"] for p in proposed):
        out.append("CB-230 keep / partner / stop is due before the January board. Put it on the pack?")
    coupled = sum(1 for r in inflow if r.get("relation") != "unclassified")
    if coupled and not out:
        out.append(f"{coupled} Helen items couple to the current goal. Accept the compiled performance lines, or request changes?")
    return out[:3]


def branches(proposed: list[dict], published: list[str]) -> list[str]:
    out = []
    pub = " ".join(published).lower()
    for item in proposed:
        line = item["line"]
        if line.lower() not in pub:
            out.append(f"Branch · {line} Nobody accepted this onto the goal.")
    return out[:3]


def conflicts(inflow: list[dict], published: list[str], proposed: list[dict]) -> list[str]:
    unclass = sum(1 for r in inflow if r.get("relation") == "unclassified")
    coupled = sum(1 for r in inflow if r.get("relation") != "unclassified")
    out = []
    if unclass > coupled:
        out.append(
            f"Helen's inflow mostly unclassified ({unclass}) against the published goal ({coupled} coupled). The seed OKRs and her files are on different work."
        )
    pub = " ".join(published)
    if proposed and pub and proposed[0]["line"] not in pub:
        out.append("Performance compiled from Helen does not match the goal in beef/goals.md.")
    return out[:3]


def payload(
    *,
    pulled_at: str,
    review: dict,
    published: list[str],
    proposed: list[dict],
    declined: list[str],
    comments: str,
    inflow: list[dict],
    history: list[str],
    events_n: int,
    emails_n: int,
) -> dict:
    index = by_id(inflow)
    coupled = sum(1 for r in inflow if r.get("relation") != "unclassified")
    unclass = sum(1 for r in inflow if r.get("relation") == "unclassified")
    rows = diff_rows(published, proposed, index)
    added = sum(1 for r in rows if r["right"] and r["right"]["kind"] == "add")
    removed = sum(1 for r in rows if r["left"] and r["left"]["kind"] == "del")
    return {
        "title": "Strategy update",
        "date": display_date(pulled_at),
        "status": "open",
        "snapshot": pulled_at,
        "chiefCalls": 0,
        "context": {
            "events": events_n,
            "emails": emails_n,
            "coupled": coupled,
            "unclassified": unclass,
        },
        "decisions": decisions(published, proposed, inflow),
        "effort": effort_bars(published, inflow),
        "people": people_from_inflow(inflow),
        "branches": branches(proposed, published),
        "conflicts": conflicts(inflow, published, proposed),
        "files": [
            {
                "name": "Priorities | Performance",
                "added": added,
                "removed": removed,
                "rows": rows,
            }
        ],
        "history": history
        or [
            f"{pulled_at} · this brief is open. No Accept yet.",
        ],
        "lastReview": review["action"],
        "reviewNotes": comments if review["action"] != "none" else "",
        "declined": declined,
        "published": published,
        "proposed": [p["line"] for p in proposed],
    }


def render_md(data: dict, proposed: list[dict]) -> str:
    lines = [
        "# Chief Brief",
        "",
        "Chief Brief page payload, built from [Chief Beef](../beef/CHIEF_BEEF.md).",
        "The app reads `public/brief.json` (same compile). `/chief` reads `beef/goals.md`.",
        "",
        f"- Status: **{data['status']}** (last review: `{data['lastReview']}`)",
        f"- Snapshot: `{data['snapshot']}`",
        f"- `/chief` calls: **{data['chiefCalls']} recorded**",
        f"- Helen context: {data['context']['events']} events, {data['context']['emails']} emails, "
        f"{data['context']['coupled']} coupled, {data['context']['unclassified']} unclassified",
        "",
        "## 1. Decisions needed",
        "",
    ]
    if data["decisions"]:
        for i, d in enumerate(data["decisions"], 1):
            lines.append(f"{i}. {d}")
    else:
        lines.append("_None._")
    lines += ["", "## 2. Effort by OKR (Helen inflow)", ""]
    for bar in data["effort"]:
        lines.append(f"- {bar['name']}: {bar['count']}")
    lines += ["", "## 3. What people are doing (from inflow)", ""]
    for p in data["people"]:
        lines.append(f"- {p['name']} ({p['tag']}, {p['count']} items): {p['work']}")
    lines += ["", "## 4. Merge conflicts", ""]
    if data["conflicts"]:
        for c in data["conflicts"]:
            lines.append(f"- {c}")
    else:
        lines.append("_None from Helen inflow._")
    lines += ["", "## 5. Goal (`beef/goals.md`)", ""]
    if data["published"]:
        for i, o in enumerate(data["published"], 1):
            lines.append(f"{i}. {o}")
    else:
        lines.append("_none_")
    lines += ["", "## Proposed performance (from Helen’s mail and calendar)", ""]
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
        "| Priorities (goal) | Performance (Helen snapshot) |",
        "| --- | --- |",
    ]
    n = max(len(data["published"]), len(proposed))
    for i in range(n):
        left = data["published"][i] if i < len(data["published"]) else "—"
        right = proposed[i]["line"] if i < len(proposed) else "—"
        lines.append(f"| {left} | {right} |")
    lines += ["", "## Blame", "", "Helen evidence ids are on each Performance line.", "", "## History", ""]
    for h in data["history"]:
        lines.append(f"- {h}")
    lines += [
        "",
        "## If leadership Accepts",
        "",
        "Write the Performance column into `beef/goals.md`. The next `/chief` reads that goal. The brief recompiles from Beef.",
        "",
        "## Last review",
        "",
        f"Action: `{data['lastReview']}`",
        "",
    ]
    if data.get("reviewNotes"):
        lines.append("```")
        lines.append(data["reviewNotes"][:4000])
        lines.append("```")
        lines.append("")
    if data.get("declined"):
        lines.append("## Declined (do not re-propose)")
        lines.append("")
        for d in data["declined"]:
            lines.append(f"- {d}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def compile_brief(root: Path) -> dict:
    plan = (root / "plan.md").read_text(encoding="utf-8")
    review_text = (root / "briefs" / "REVIEW.md").read_text(encoding="utf-8")
    review = latest_review(review_text)
    declined = declined_lines(root / "briefs" / "declined.md")
    ids = load_ids(root)
    inflow = load_jsonl(root / "beef" / "inflow.jsonl")
    events_n = sum(1 for r in inflow if r.get("source") == "calendar")
    emails_n = sum(1 for r in inflow if r.get("source") == "email")
    goals_path = root / "beef" / "goals.md"
    if goals_path.exists():
        published = parse_okrs(goals_path.read_text(encoding="utf-8"))
    else:
        published = parse_okrs(plan)

    proposed = []
    for item in HELEN_LINES:
        if any(item["line"] == d or d in item["line"] for d in declined):
            continue
        present = [e for e in item["evidence"] if e in ids]
        if not present:
            continue
        proposed.append({**item, "evidence": present})

    data = payload(
        pulled_at=manifest_pulled_at(root),
        review=review,
        published=published,
        proposed=proposed,
        declined=declined,
        comments=review.get("raw") or "",
        inflow=inflow,
        history=review_history(review_text),
        events_n=events_n,
        emails_n=emails_n,
    )
    md = render_md(data, proposed)
    briefs = root / "briefs"
    briefs.mkdir(parents=True, exist_ok=True)
    (briefs / "pending.md").write_text(md, encoding="utf-8")
    (briefs / "pending.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    public = root / "public"
    public.mkdir(parents=True, exist_ok=True)
    (public / "brief.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    data = compile_brief(args.root)
    print(
        f"wrote briefs/pending.md, public/brief.json "
        f"({len(data['proposed'])} proposed lines, {data['context']['coupled']} coupled)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
