#!/usr/bin/env python3
"""Pull Helen's bio MCP into data/canon and data/raw.

Does not write briefs/ or plan.md. Cloud-safe: HTTP JSON-RPC, stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BIO_URL = "https://bio.esconsulting.io/mcp"
BIO_AUTH = "Bearer HelenMCP"
WINDOW_START = date(2026, 6, 1)
WINDOW_END = date(2026, 10, 31)
CAL_DAYS = 7
INBOX_DAYS = 3
EMAIL_CAP = 200
CAL_CAP = 200


class BioClient:
    def __init__(self, url: str = BIO_URL, auth: str = BIO_AUTH) -> None:
        self.url = url
        self.auth = auth
        self._id = 0
        self._initialized = False

    def _rpc(self, method: str, params: dict | None = None) -> object:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": self.auth,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "es-hackathon-ingest/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raise SystemExit(f"MCP HTTP {e.code} on {method}: {e.read()[:400]!r}") from e
        data = _parse_rpc_body(raw)
        if "error" in data:
            raise SystemExit(f"MCP error on {method}: {data['error']}")
        return data.get("result")

    def initialize(self) -> None:
        if self._initialized:
            return
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "es-hackathon-ingest", "version": "0.1"},
            },
        )
        note = urllib.request.Request(
            self.url,
            data=json.dumps(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            ).encode(),
            headers={
                "Authorization": self.auth,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "es-hackathon-ingest/0.1",
            },
            method="POST",
        )
        try:
            urllib.request.urlopen(note, timeout=30).read()
        except urllib.error.HTTPError:
            pass
        self._initialized = True

    def call_tool(self, name: str, arguments: dict) -> object:
        self.initialize()
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        return _unwrap_tool_result(result)

    def read_resource(self, uri: str) -> str:
        self.initialize()
        result = self._rpc("resources/read", {"uri": uri})
        contents = (result or {}).get("contents") or []
        parts = []
        for item in contents:
            if item.get("text"):
                parts.append(item["text"])
        return "\n".join(parts)


def _parse_rpc_body(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("event:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        raise SystemExit(f"SSE body had no data: {raw[:200]!r}")
    return json.loads(raw)


def _unwrap_tool_result(result: object) -> object:
    if not isinstance(result, dict):
        return result
    if "structuredContent" in result and result["structuredContent"] is not None:
        return result["structuredContent"]
    chunks = []
    for item in result.get("content") or []:
        if item.get("type") == "text" and item.get("text"):
            chunks.append(item["text"])
    text = "\n".join(chunks).strip()
    if not text:
        return result
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def daterange_windows(start: date, end: date, days: int):
    cur = start
    while cur <= end:
        window_end = min(cur + timedelta(days=days - 1), end)
        yield cur, window_end
        cur = window_end + timedelta(days=1)


def _maybe_split(start: date, end: date) -> list[tuple[date, date]]:
    if start >= end:
        return [(start, end)]
    mid = start + (end - start) / 2
    return [(start, mid), (mid + timedelta(days=1), end)]


def pull_events(client: BioClient) -> list[dict]:
    by_id: dict[str, dict] = {}
    for start, end in daterange_windows(WINDOW_START, WINDOW_END, CAL_DAYS):
        _pull_events_window(client, start, end, by_id)
    return sorted(by_id.values(), key=lambda e: (e.get("start") or "", e.get("id") or ""))


def _pull_events_window(
    client: BioClient, start: date, end: date, by_id: dict[str, dict]
) -> None:
    payload = client.call_tool(
        "calendar_search",
        {"dates": [start.isoformat(), end.isoformat()], "mode": "events"},
    )
    events = payload.get("events") if isinstance(payload, dict) else None
    if events is None:
        raise SystemExit(f"calendar_search unexpected: {payload!r}"[:400])
    count = payload.get("count", len(events))
    print(f"  calendar {start}..{end} count={count}", file=sys.stderr)
    if count >= CAL_CAP and start < end:
        for a, b in _maybe_split(start, end):
            _pull_events_window(client, a, b, by_id)
        return
    for event in events:
        eid = event.get("id")
        if eid:
            by_id[eid] = event


def pull_emails(client: BioClient) -> list[dict]:
    by_id: dict[str, dict] = {}
    for start, end in daterange_windows(WINDOW_START, WINDOW_END, INBOX_DAYS):
        _pull_email_window(client, "inbox", start, end, by_id)
    payload = client.call_tool(
        "email_search",
        {
            "dates": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
            "folder": "sent",
            "limit": EMAIL_CAP,
        },
    )
    sent = payload.get("emails") if isinstance(payload, dict) else []
    print(f"  sent {WINDOW_START}..{WINDOW_END} count={len(sent)}", file=sys.stderr)
    for mail in sent:
        mid = mail.get("id")
        if mid:
            by_id[mid] = mail
    return sorted(by_id.values(), key=lambda m: (m.get("sent_at") or "", m.get("id") or ""))


def _pull_email_window(
    client: BioClient, folder: str, start: date, end: date, by_id: dict[str, dict]
) -> None:
    payload = client.call_tool(
        "email_search",
        {
            "dates": [start.isoformat(), end.isoformat()],
            "folder": folder,
            "limit": EMAIL_CAP,
        },
    )
    emails = payload.get("emails") if isinstance(payload, dict) else None
    if emails is None:
        raise SystemExit(f"email_search unexpected: {payload!r}"[:400])
    count = payload.get("count", len(emails))
    print(f"  {folder} {start}..{end} count={count}", file=sys.stderr)
    if count >= EMAIL_CAP and start < end:
        for a, b in _maybe_split(start, end):
            _pull_email_window(client, folder, a, b, by_id)
        return
    for mail in emails:
        mid = mail.get("id")
        if mid:
            by_id[mid] = mail


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_manifest(path: Path, events: int, emails: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "source": BIO_URL,
                "pulled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "window": {
                    "start": WINDOW_START.isoformat(),
                    "end": WINDOW_END.isoformat(),
                },
                "counts": {"events": events, "emails": emails},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Helen bio MCP snapshots")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repo root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    root: Path = args.root
    data = root / "data"
    client = BioClient()

    print("reading canon", file=sys.stderr)
    canon = client.read_resource("knowledge://continental-bio/background")
    canon_path = data / "canon" / "background.md"
    canon_path.parent.mkdir(parents=True, exist_ok=True)
    canon_path.write_text(canon.rstrip() + "\n", encoding="utf-8")

    print("pulling calendar", file=sys.stderr)
    events = pull_events(client)
    print("pulling email", file=sys.stderr)
    emails = pull_emails(client)

    write_jsonl(data / "raw" / "events.jsonl", events)
    write_jsonl(data / "raw" / "emails.jsonl", emails)
    write_manifest(data / "raw" / "manifest.json", len(events), len(emails))
    print(f"wrote {len(events)} events, {len(emails)} emails → {data}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
