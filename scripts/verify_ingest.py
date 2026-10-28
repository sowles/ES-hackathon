#!/usr/bin/env python3
"""End-to-end check: snapshot files vs live bio MCP.

Exit 0 if the local JSONL matches live pulls on sampled windows and known ids.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_bio import BioClient, WINDOW_END, WINDOW_START  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def main() -> int:
    events_path = ROOT / "data" / "raw" / "events.jsonl"
    emails_path = ROOT / "data" / "raw" / "emails.jsonl"
    canon_path = ROOT / "data" / "canon" / "background.md"
    if not events_path.exists() or not emails_path.exists():
        fail("run scripts/ingest_bio.py first")

    events = load_jsonl(events_path)
    emails = load_jsonl(emails_path)
    event_ids = [e.get("id") for e in events]
    email_ids = [m.get("id") for m in emails]

    if not events:
        fail("no events")
    if not emails:
        fail("no emails")
    if len(event_ids) != len(set(event_ids)):
        fail("duplicate event ids")
    if len(email_ids) != len(set(email_ids)):
        fail("duplicate email ids")
    ok(f"unique ids events={len(events)} emails={len(emails)}")

    for e in events:
        for key in ("id", "title", "start", "date"):
            if not e.get(key):
                fail(f"event {e.get('id')} missing {key}")
        if not (e.get("id") or "").startswith("cron-event-") and not e.get("summary"):
            fail(f"event {e.get('id')} missing summary")
        d = date.fromisoformat(e["date"])
        if d < WINDOW_START or d > WINDOW_END:
            fail(f"event {e['id']} date {d} outside window")
    ok("event schema + window")

    for m in emails:
        for key in ("id", "subject", "sent_at", "folder"):
            if not m.get(key):
                fail(f"email {m.get('id')} missing {key}")
    folders = {m["folder"] for m in emails}
    if "sent" not in folders or "inbox" not in folders:
        fail(f"expected inbox+sent, got {folders}")
    ok(f"email schema folders={sorted(folders)}")

    canon = canon_path.read_text(encoding="utf-8")
    if "Continental Bio" not in canon or "Helen Williamson" not in canon:
        fail("canon missing company/Helen")
    ok("canon")

    known_events = {"event-0001", "event-0002"}
    missing_e = known_events - set(event_ids)
    if missing_e:
        fail(f"missing known events {missing_e}")
    known_mail = {"email-0024", "email-0013"}
    missing_m = known_mail - set(email_ids)
    if missing_m:
        fail(f"missing known sent mail {missing_m}")
    ok("known ids present")

    # Live MCP: a capped full-range calendar pull must be a *subset* of our paged snapshot.
    client = BioClient()
    live_cal = client.call_tool(
        "calendar_search",
        {
            "dates": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
            "mode": "events",
        },
    )
    live_events = live_cal.get("events") or []
    live_ids = {e["id"] for e in live_events}
    snapshot_ids = set(event_ids)
    missing_live = live_ids - snapshot_ids
    if missing_live:
        fail(f"paged snapshot missing {len(missing_live)} ids from uncapped-range live pull: {sorted(missing_live)[:8]}")
    if live_cal.get("count") == 200 and len(events) <= 200:
        fail("snapshot still looks cap-truncated (≤200) while live range also hit 200")
    ok(f"live full-range calendar ({len(live_ids)} capped) ⊆ snapshot ({len(snapshot_ids)})")

    # Live 7-day window should match snapshot for that week exactly.
    week = client.call_tool(
        "calendar_search",
        {"dates": ["2026-06-02", "2026-06-08"], "mode": "events"},
    )
    week_ids = {e["id"] for e in week.get("events") or []}
    snap_week = {
        e["id"]
        for e in events
        if "2026-06-02" <= e["date"] <= "2026-06-08"
    }
    if week_ids != snap_week:
        fail(
            f"week 2026-06-02..08 live={sorted(week_ids)} snap={sorted(snap_week)}"
        )
    ok(f"week calendar exact match ({len(week_ids)} events)")

    live_sent = client.call_tool(
        "email_search",
        {
            "dates": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
            "folder": "sent",
            "limit": 200,
        },
    )
    sent_live = {m["id"] for m in live_sent.get("emails") or []}
    sent_snap = {m["id"] for m in emails if m.get("folder") == "sent"}
    if sent_live != sent_snap:
        fail(f"sent mismatch live={len(sent_live)} snap={len(sent_snap)}")
    ok(f"sent folder exact match ({len(sent_snap)})")

    inbox_live = client.call_tool(
        "email_search",
        {
            "dates": ["2026-10-20", "2026-10-22"],
            "folder": "inbox",
            "limit": 200,
        },
    )
    inbox_ids = {m["id"] for m in inbox_live.get("emails") or []}
    snap_all = set(email_ids)
    missing_inbox = inbox_ids - snap_all
    if missing_inbox:
        fail(f"inbox 2026-10-20..22 live ids missing from snapshot: {sorted(missing_inbox)[:8]}")
    ok(f"inbox 3-day live pull ⊆ snapshot ({len(inbox_ids)} ids)")

    # Spot-check body of a known sent mail against live.
    live_one = next(m for m in live_sent["emails"] if m["id"] == "email-0024")
    snap_one = next(m for m in emails if m["id"] == "email-0024")
    if live_one.get("subject") != snap_one.get("subject"):
        fail("email-0024 subject drift")
    if (live_one.get("body") or "")[:80] != (snap_one.get("body") or "")[:80]:
        fail("email-0024 body drift")
    ok("email-0024 subject/body match live")

    print("PASS ingest matches live bio MCP on sampled windows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
