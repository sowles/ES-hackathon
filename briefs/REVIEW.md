# Chief Brief review log

Append-only. The morning ingest agent reads the **latest** entry before drafting `pending.md`.

Format:

```
## YYYY-MM-DDTHH:MM:SSZ — accept | request-changes | decline
Reviewer:
Brief: briefs/pending.md (or archived path)
Notes:
- …
Lines accepted / kept / dropped / rewritten:
- …
```

## Entries

_None yet. Until the first review, the morning agent may create `briefs/pending.md` against Current OKRs in `plan.md`._
