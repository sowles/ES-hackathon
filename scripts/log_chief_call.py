#!/usr/bin/env python3
"""Context and call log for /chief. Never writes beef/goals.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VERDICTS = {"on", "beside", "conflict", "unclassified"}
STANCES = {"for", "against"}
REVIEW_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) — (accept|request-changes|decline)\s*$",
    re.M,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def goals_text(root: Path) -> str:
    path = root / "beef" / "goals.md"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    return path.read_text(encoding="utf-8")


def load_calls(root: Path) -> list[dict]:
    path = root / "beef" / "calls.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_reviews(root: Path) -> list[dict]:
    path = root / "briefs" / "REVIEW.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    marks = list(REVIEW_RE.finditer(text))
    entries = []
    for i, mark in enumerate(marks):
        start = mark.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        entries.append(
            {
                "at": mark.group(1),
                "action": mark.group(2),
                "body": text[start:end].strip(),
            }
        )
    return entries


def opening(engineer: str, previous_at: str | None, reviews: list[dict]) -> str:
    if not reviews or not engineer:
        return ""
    parts = []
    last = reviews[-1]
    if last["action"] == "request-changes" and engineer.lower() in last["body"].lower():
        parts.append("Request changes:\n" + last["body"])
    if previous_at:
        accepts = [entry for entry in reviews if entry["action"] == "accept"]
        if accepts and accepts[-1]["at"] > previous_at:
            accepted = accepts[-1]
            parts.insert(
                0,
                "Plan changed since your last call.\n"
                + accepted["at"]
                + " accept\n"
                + accepted["body"],
            )
    return "\n\n".join(parts)


def cmd_context(root: Path, engineer: str) -> None:
    print(goals_text(root).rstrip())
    print("\n--- calls ---")
    calls = load_calls(root)
    if not calls:
        print("none")
    else:
        for call in calls[-30:]:
            brief = {
                "id": call.get("id"),
                "at": call.get("at"),
                "engineer": call.get("engineer"),
                "change": call.get("change"),
                "placements": call.get("placements"),
            }
            print(json.dumps(brief, ensure_ascii=False))
    print("\n--- review ---")
    reviews = load_reviews(root)
    if not reviews:
        print("none")
    else:
        last = reviews[-1]
        print(f"{last['at']} {last['action']}\n{last['body']}")
    if not engineer:
        return
    previous = [call for call in calls if call.get("engineer") == engineer]
    print("\n--- this engineer ---")
    previous_at = previous[-1]["at"] if previous else None
    print("no previous call" if previous_at is None else previous[-1]["at"])
    text = opening(engineer, previous_at, reviews)
    print("\n--- open the reply with ---")
    print(text or "none")


def require_text(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{key} is required")
    return value.strip()


def validate(payload: dict, goals: str) -> dict:
    engineer = require_text(payload, "engineer")
    prd = require_text(payload, "prd")
    change = require_text(payload, "change")
    placements = payload.get("placements")
    if not isinstance(placements, list) or not placements:
        raise SystemExit("placements must be a non-empty list")
    clean = []
    for placement in placements:
        if not isinstance(placement, dict):
            raise SystemExit("each placement must be an object")
        verdict = placement.get("verdict")
        stance = placement.get("stance")
        if verdict not in VERDICTS:
            raise SystemExit(f"verdict must be one of {sorted(VERDICTS)}")
        if stance not in STANCES:
            raise SystemExit("stance must be for or against")
        if verdict == "unclassified":
            clean.append({"verdict": verdict, "okr": None, "okr_line": "", "stance": stance, "proposed_line": ""})
            continue
        okr = placement.get("okr")
        if okr not in (1, 2, 3):
            raise SystemExit("okr must be 1, 2, or 3")
        okr_line = placement.get("okr_line")
        proposed = placement.get("proposed_line")
        if not isinstance(okr_line, str) or okr_line.strip() not in goals:
            raise SystemExit("okr_line must be quoted from beef/goals.md")
        if not isinstance(proposed, str) or not proposed.strip():
            raise SystemExit("proposed_line is required")
        clean.append(
            {
                "verdict": verdict,
                "okr": okr,
                "okr_line": okr_line.strip(),
                "stance": stance,
                "proposed_line": proposed.strip(),
            }
        )
    others = payload.get("engineers_on_work") or []
    if not isinstance(others, list) or not all(isinstance(name, str) and name.strip() for name in others):
        raise SystemExit("engineers_on_work must be a list of names")
    return {
        "engineer": engineer,
        "prd": prd,
        "change": change,
        "placements": clean,
        "engineers_on_work": [name.strip() for name in others],
    }


def sentiment(calls: list[dict], record: dict) -> str:
    lines = ["This call does not move the goal. One call is not enough to move an OKR."]
    seen = []
    for placement in record["placements"]:
        okr = placement["okr"]
        if okr is None or okr in seen:
            continue
        seen.append(okr)
        fors: set[str] = set()
        against: set[str] = set()
        for call in calls:
            for older in call.get("placements") or []:
                if older.get("okr") != okr:
                    continue
                if older.get("stance") == "for":
                    fors.add(call["id"])
                elif older.get("stance") == "against":
                    against.add(call["id"])
        lines.append(f"OKR {okr}: {len(fors)} for, {len(against)} against.")
    if any(placement["verdict"] == "unclassified" for placement in record["placements"]):
        lines.append("Unclassified placements are not counted toward an OKR.")
    return "\n".join(lines)


def cmd_log(root: Path, raw: str) -> None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"call JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("call JSON must be an object")
    goals = goals_text(root)
    record = validate(payload, goals)
    calls = load_calls(root)
    previous = [call for call in calls if call.get("engineer") == record["engineer"]]
    previous_at = previous[-1]["at"] if previous else None
    record["id"] = f"call-{len(calls) + 1:04d}"
    record["at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = root / "beef" / "calls.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    calls.append(record)
    print(f"logged {record['id']} at {record['at']}")
    print("\n--- sentiment ---")
    print(sentiment(calls, record))
    print("\n--- open the reply with ---")
    print(opening(record["engineer"], previous_at, load_reviews(root)) or "none")
    print("\n--- goal was not edited ---")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read Chief context or append one /chief call.")
    parser.add_argument("--root", type=Path, default=repo_root())
    sub = parser.add_subparsers(dest="cmd", required=True)
    context = sub.add_parser("context")
    context.add_argument("--engineer", default="")
    sub.add_parser("log")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.cmd == "context":
        cmd_context(root, args.engineer.strip())
    else:
        cmd_log(root, sys.stdin.read())


if __name__ == "__main__":
    main()
