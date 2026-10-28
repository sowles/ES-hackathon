#!/usr/bin/env python3
"""Receive hackathon Slack host events and reply as Chief.

Ignores type=ping. Auth: Authorization Bearer $WEBHOOK_KEY.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


ENV = load_env(ROOT / ".env")
WEBHOOK_KEY = ENV.get("WEBHOOK_KEY", "")
PORT = int(os.environ.get("PORT", "8787"))

MENTION = re.compile(r"<@[^>]+>\s*")
CMD = re.compile(
    r"^\s*/?(chief-brief|brief|chief)\b[\s:,-]*(.*)$",
    re.I | re.S,
)


def strip_text(event: dict) -> str:
    blob = event.get("event") or event
    text = blob.get("clean_text") or blob.get("text") or event.get("text") or ""
    return MENTION.sub("", text).strip()


def chief_reply(prd: str) -> tuple[str, list]:
    prd = prd.strip() or "(no PRD text)"
    text = (
        "Chief · PRD check\n"
        f"Change: {prd}\n"
        "Verdict: on OKR 1 (site), beside OKR 1 (Primer3), in conflict with OKR 3 "
        "(runway 11 months vs floor of 12).\n"
        "Engineers: Jordan + Owen on the site, Nate on Primer3, Sam on runway, Alex on supply.\n"
        "Sentiment: 2 to open in November, 1 against a second site, 1 runway miss, 1 for Primer3.\n"
        "This reply does not change the goal. Leadership accepts on /brief."
    )
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Chief · PRD check"}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Change*\n{prd[:500]}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*Verdict*\nOn OKR 1 · beside OKR 1 · conflict OKR 3"},
                {"type": "mrkdwn", "text": "*OKR 3*\nRunway 11 months if the site opens. Floor is 12."},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Engineers on nearby work*\n"
                    "• *Jordan Hale* — open the site in November. Supply covers Q1.\n"
                    "• *Owen Briggs* — enrollment on the October plan. No second site.\n"
                    "• *Nate Adler* — Primer3 for agents. Beside OKR 1.\n"
                    "• *Sam Pell* — runway falls to 11 months.\n"
                    "• *Alex Ruiz* — months of supply still clears 3 in November."
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Sentiment: 2 open / 1 no second site / 1 runway miss / 1 Primer3. Plan unchanged until /brief is accepted.",
                }
            ],
        },
    ]
    return text, blocks


def brief_reply() -> tuple[str, list]:
    text = (
        "Chief Brief · open · 5 /chief calls in the seed batch. "
        "Priorities: open the November site (conflict with runway 12). "
        "Accept is not wired from Slack yet."
    )
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Chief Brief · open"}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*Calls*\n5 /chief (seed)"},
                {"type": "mrkdwn", "text": "*State*\nOpen · not accepted"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*What engineers are doing*\n"
                    "• Site (Jordan, Owen) — on OKR 1\n"
                    "• Supply (Alex) — on OKR 2\n"
                    "• Runway (Sam) — on OKR 3, fights November open\n"
                    "• Primer3 (Nate) — beside OKR 1"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Priorities* (proposed)\n"
                    "~Hold the new site until months of supply stay above 3~\n"
                    "*Open the new site in November. Supply covers Q1.*\n"
                    "*Let lab agents run Primer3.*"
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Accept still happens in the Chief Brief page, not in Slack. This message does not write beef/goals.md.",
                }
            ],
        },
    ]
    return text, blocks


def help_reply() -> tuple[str, list]:
    text = "Chief: /chief <PRD> for engineers. /brief or /chief-brief for leaders."
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Chief"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Engineers*\n`/chief` plus a PRD. I place it on the OKRs and name who is already on that work.\n\n"
                    "*Leaders*\n`/brief` or `/chief-brief`. I show the pull-request view of the plan. I do not change the goal until someone accepts the brief."
                ),
            },
        },
    ]
    return text, blocks


def post_reply(reply_url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        reply_url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "raw": raw[:300]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[webhook]", fmt % args)

    def _auth_ok(self) -> bool:
        if not WEBHOOK_KEY:
            return False
        got = self.headers.get("Authorization", "")
        return got == f"Bearer {WEBHOOK_KEY}"

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def _send(self, code: int, body: dict | None = None) -> None:
        blob = json.dumps(body or {}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def do_GET(self) -> None:
        self._send(200, {"ok": True, "service": "chief-slack-webhook"})

    def do_POST(self) -> None:
        if not self._auth_ok():
            self._send(401, {"ok": False, "error": "unauthorized"})
            return
        event = self._read_json()
        etype = str(event.get("type") or "")
        if etype == "ping" or event.get("is_ping"):
            self._send(200, {"ok": True, "ignored": "ping"})
            return

        reply_url = event.get("reply_url")
        reply_token = event.get("reply_token")
        if not reply_url or not reply_token:
            self._send(200, {"ok": True, "ignored": "no_reply"})
            return

        text = strip_text(event)
        m = CMD.match(text)
        if not m:
            body_text, blocks = help_reply()
        else:
            cmd, rest = m.group(1).lower(), m.group(2).strip()
            if cmd in ("brief", "chief-brief"):
                body_text, blocks = brief_reply()
            else:
                body_text, blocks = chief_reply(rest)

        payload = {"reply_token": reply_token, "text": body_text, "blocks": blocks}
        try:
            result = post_reply(reply_url, payload)
            if not result.get("ok", True) and result.get("slack_error"):
                post_reply(reply_url, {"reply_token": reply_token, "text": body_text})
        except Exception as exc:
            print("[webhook] reply failed", type(exc).__name__)
            self._send(200, {"ok": False, "error": "reply_failed"})
            return
        self._send(200, {"ok": True})


def main() -> None:
    if not WEBHOOK_KEY:
        raise SystemExit("WEBHOOK_KEY missing in .env")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"chief webhook on :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
