# Morning ingest → Chief Brief payload

Weekdays 08:00 America/New_York.

`/chief` scores PRDs against **Current OKRs in plan.md** until Accept. This job refreshes **`briefs/pending.md`**, the Chief Brief page payload. It never Accepts and never edits those OKRs.

```
python3 scripts/run_morning.py
```

Ingest Helen → signals → rewrite `briefs/pending.md` from the last `briefs/REVIEW.md` action.

If the latest review is Accept, `plan.md` must already show the accepted lines; if it does not, stop and report the mismatch.
