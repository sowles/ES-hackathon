# Helen data ingestion (for agents)

How we pull CEO context for `/chief` and `/brief`. Product contract is [plan.md](../plan.md). Helen-shaped OKRs (exercise) are [helen-okr-pack-h2-2026.md](helen-okr-pack-h2-2026.md).

`/chief` is the user command. It scores a PRD against **Current OKRs in plan.md** until leadership Accepts a Brief (`unclassified` is allowed; never force a weak match). After Accept, the next `/chief` opens with "Plan changed since your last call."

Morning ingest rewrites **`briefs/pending.md`**, the payload for the Chief Brief page (diff, decisions needed, blame from Helen ids). It never Accepts and never edits Current OKRs.

## Where to look

| Path | What it is |
| --- | --- |
| `data/canon/background.md` | Company canon from `knowledge://continental-bio/background` |
| `data/raw/events.jsonl` | Helen’s calendar, one event per line. Each row already has the meeting `summary`. |
| `data/raw/emails.jsonl` | Mailbox snapshot (`inbox` + `sent`) |
| `data/derived/signals.md` | Ranked decisions with evidence ids |
| `briefs/pending.md` | Chief Brief payload. Morning ingest rewrites this. |
| `briefs/REVIEW.md` | Accept / Request changes / Decline log. Morning job starts here. |
| `briefs/declined.md` | Lines leadership declined; do not re-propose without new evidence |
| `briefs/accepted/` | History of accepted plan versions (who / when) |
| `plan.md` Current OKRs | **Published plan. `/chief` reads this.** |

Refresh:

```
python3 scripts/run_morning.py          # ingest + signals + rewrite briefs/pending.md
python3 scripts/verify_ingest.py        # snapshot vs live MCP
```

`verify_ingest.py` checks unique ids, known records, a calendar week, sent mail, and an inbox window. Future `cron-event-*` rows may have empty summaries; that is the source, not a paging bug.

## Source: bio MCP (no Slack)

Helen Williamson **is** the CEO. There is no Slack or chat in this connector.

- URL: `https://bio.esconsulting.io/mcp`
- Header: `Authorization: Bearer HelenMCP`
- Cursor server name: `bio`

Tools:

- `calendar_search` — primary for meetings. Summaries are on the events. **Do not** also pull `meeting_summary_search` (same text, 50-item cap).
- `email_search` — `folder`: `inbox` \| `sent` \| `archive`. Archive is empty. Sent is small and highest signal. Inbox mixes `backfill-*` corpus and daily `cron-*` pings.
- Resource `knowledge://continental-bio/background`

Caps: calendar **200**, email **200**, summaries **50**.

Paging (required or you silently drop history):

- Calendar: 7-day windows, `2026-06-01` through `2026-10-31`
- Inbox: 3-day windows
- Sent: one range pull is enough
- Dedupe on `id`

Cloud / morning jobs must call HTTP JSON-RPC. Do not assume a local Cursor MCP session.

## How to rank evidence

1. Helen **sent** mail
2. Board chair, October board rehearsal, Pipeline council, Cash and earn-out, CB-230 keep-or-stop
3. GSK alliance, Harbor slot, clinical/regulatory 1:1s
4. Skip “Schedule review with Nate” unless it states a decision
5. `cron-*` inbox is today’s pulse, not 3-year-plan material

Tags: `CB-101/TSA`, `CB-201/Harbor`, `CB-214`, `CB-230`, `cash/runway`, `board`, `people`.

Do not invent AtScale / warehouse numbers. Live warehouse numbers are out of scope for the brief (plan.md).

## Morning agent (weekdays 08:00 ET)

Overnight staffer. Never Accepts. Never posts Request-changes comments to Slack (Brief UI does that).

1. Read latest `briefs/REVIEW.md` and published OKRs in `plan.md`. If the last action is Accept and `plan.md` does not match, **stop** and report the mismatch.
2. Load `briefs/declined.md` and any request-changes comments.
3. Re-ingest the **full** bio window (not a watermark).
4. Rebuild `signals.md`.
5. Rewrite `briefs/pending.md` in the plan.md Brief shape: decisions needed, effort-by-OKR (seed until call log exists), merge conflicts from plan.md, Priorities \| Performance from Helen vs published OKRs, history pointer.

| Last review | Tomorrow |
| --- | --- |
| Accept | Diff new Helen evidence vs **published** `plan.md`. Do not reopen accepted lines unless new mail/calendar contradicts them. Next `/chief` must be able to say the plan changed. |
| Request changes | Plan unchanged. Rebuild pending from old plan using the reviewer’s comments. |
| Decline | Plan unchanged. Do not re-propose declined lines unless a **new** email/event id appears after the decline. |

`draft_brief.py` inputs: `plan.md` → latest `REVIEW.md` → `declined.md` → snapshot ids. Output: `briefs/pending.md` only.

## Out of scope for ingest

No Slack adapter, no `/chief` verdict engine (on / beside / conflict / unclassified), no Brief website, no database, no writes back to Helen’s mailbox, no auto-accept.
