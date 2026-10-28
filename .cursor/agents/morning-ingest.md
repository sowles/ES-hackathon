# Morning pipeline: context into Chief Beef, then compile the Brief

Weekdays 08:00 America/New_York. No person maintains Beef. This job never changes the **goal**.

```
python3 scripts/run_morning.py
```

1. Pull Helen (`ingest_bio.py`).
2. Rebuild signals.
3. Write context to `beef/inflow.jsonl` and refresh the context half of `beef/CHIEF_BEEF.md`. Do **not** edit `beef/goals.md`.
4. Compile `briefs/pending.md` from Beef. Do not Accept.
