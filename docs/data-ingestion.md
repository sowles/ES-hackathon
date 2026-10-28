# Helen data ingestion (for agents)

How we pull CEO context for `/chief` and `/brief`. Product contract is [plan.md](../plan.md). Helen-shaped OKRs (exercise) are [helen-okr-pack-h2-2026.md](helen-okr-pack-h2-2026.md).

This pipeline does **not** replace `/chief`. It feeds evidence and a **pending Brief**. Only an Accept on Chief Brief republishes the plan.

## Where to look

| Path | What it is |
| --- | --- |
| `data/canon/background.md` | Company canon from `knowledge://continental-bio/background` |
| `data/raw/events.jsonl` | Helen’s calendar, one event per line. Each row already has the meeting `summary` (Decisions / Action items / Follow-ups). |
| `data/raw/emails.jsonl` | Mailbox snapshot (`inbox` + `sent`) |
| `data/derived/signals.md` | Ranked open/locked decisions, 2026–27 commitments, 2027–29 themes, with evidence ids |
| `briefs/pending.md` | Unreviewed Chief Brief (Priorities \| Performance diff) |
| `briefs/REVIEW.md` | Append-only Accept / Request changes / Decline log. **Morning agent starts here.** |
| `briefs/declined.md` | Lines leadership declined; do not re-propose without new evidence |
| `briefs/accepted/` | Archived briefs after Accept |
| `plan.md` Current OKRs | Published plan. `/chief` reads this, not the pending brief |

Refresh snapshots:

```
python3 scripts/ingest_bio.py
python3 scripts/extract_signals.py
```

These two scripts are the ingestion contract. They do not edit `plan.md` or `briefs/pending.md`.

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

Do not invent AtScale / warehouse numbers here. George’s brief is out of scope for live warehouse data.

## Morning agent (weekdays 08:00 ET)

Overnight staffer. Never Accepts.

1. Read latest `briefs/REVIEW.md` and published OKRs in `plan.md`. If the last action is Accept and `plan.md` does not match, **stop** and report the mismatch.
2. Load `briefs/declined.md` and any request-changes comments.
3. Re-ingest the **full** bio window (not a watermark).
4. Rebuild `signals.md`.
5. Write `briefs/pending.md` from the **reviewed** plan, not from yesterday’s unreviewed draft (unless still waiting on a review — then **append** overnight evidence, do not clobber the queue).

| Last review | Tomorrow |
| --- | --- |
| Accept | Diff new evidence vs **published** `plan.md`. Do not reopen accepted lines unless new mail/calendar contradicts them. |
| Request changes | Plan unchanged. Rebuild pending from old plan using the reviewer’s keep / drop / rewrite comments. Cite the comment on rewritten lines. |
| Decline | Plan unchanged. Do not re-propose declined lines unless a **new** email/event id appears after the decline. |

`draft_brief.py` inputs, in order: `plan.md` → latest `REVIEW.md` → `declined.md` → `signals.md`. Output: `briefs/pending.md` only.

## `/chief` and `/brief`

- `/chief` takes a PRD, scores it against **published** OKRs in `plan.md`, and stores the call. It does not mutate the plan.
- `/brief` shows engineer calls plus the pending Priorities \| Performance diff. Accept republishes `plan.md` and appends `briefs/REVIEW.md`.
- Until Accept, `/chief` still uses the old OKRs.

George’s `plan.md` seed OKRs are still the Mission 2 lines (trial site, months of supply, runway). The first accepted Brief on the CoS route should replace that seed with Helen’s pack so `/chief` scores the right company.

## Out of scope

No Slack adapter, no database, no live MCP on every `/chief`, no writes back to Helen’s mailbox/calendar, no auto-accept.
