# Morning ingest (data only)

Weekdays 08:00 America/New_York. You own **snapshots**, not `/chief` or Chief Brief UI.

1. From repo root: `python3 scripts/ingest_bio.py`
2. Then: `python3 scripts/extract_signals.py`
3. Do **not** edit `plan.md` Current OKRs.
4. Do **not** Accept a brief. Do **not** overwrite `briefs/pending.md` unless the brief owner’s `draft_brief.py` exists and you are explicitly running it — other agents own that file.
5. Leave `data/raw/` and `data/derived/signals.md` as the contract for `/chief` and `/brief`.

Read [docs/data-ingestion.md](../../docs/data-ingestion.md) for paging, rank order, and how Brief reviews apply once `draft_brief.py` lands.
