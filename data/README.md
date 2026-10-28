# data/

Snapshots from the bio MCP. Agents: start at [docs/data-ingestion.md](../docs/data-ingestion.md).

| Path | After first ingest |
| --- | --- |
| `canon/background.md` | Company canon |
| `raw/events.jsonl` | Calendar + meeting summaries |
| `raw/emails.jsonl` | Inbox + sent |
| `derived/signals.md` | Ranked decisions `/chief` and `/brief` should cite |

Refresh: `python3 scripts/run_morning.py` (also rebuilds Chief Beef, `briefs/pending.md`, and `public/brief.json`).
