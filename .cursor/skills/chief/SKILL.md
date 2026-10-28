---
name: chief
description: >-
  Scores one engineer PRD when the user types /chief and then the PRD.
  Reads beef/goals.md, logs the call to beef/calls.jsonl, and replies with
  the verdict, the engineers already on that work, sentiment, and the goal
  line that would change. Does not edit the goal.
---

# /chief

An engineer types `/chief` and then one PRD. Reply to that engineer. Do not edit `beef/goals.md`, `plan.md`, `briefs/pending.md`, or `briefs/REVIEW.md`.

## Input

The PRD is the rest of the message. If it is empty, ask for the PRD and stop.

The caller is a line `Engineer: Nate Adler` at the top, or a seed-batch name in the message. Seed batch: Nate Adler, Jordan Hale, Owen Briggs, Sam Pell, Alex Ruiz. If the caller is missing, ask who is calling and stop. Do not guess, and do not log.

## Read

1. Run `python3 scripts/log_chief_call.py context --engineer "Name"`.
2. Read `plan.md` from `## Seed batch` through `## Worked example`. Use a logged call over the seed last-call when both exist.
3. The goal in the script output is the only OKR text you may quote. A weak match is unclassified.

## Judge

Name the change in one sentence. For each claim in the PRD, one placement:

- `on` — the work is the OKR, inside its window.
- `beside` — useful next to an OKR, and not the OKR.
- `conflict` — the work fights an OKR line.
- `unclassified` — no line matches with confidence.

A PRD may have more than one placement. `stance` is `for` or `against` that OKR. `okr_line` is copied from `beef/goals.md`. `proposed_line` is the goal text Accept would write.

## Log

Append one call. Do not log twice.

```bash
python3 scripts/log_chief_call.py log <<'EOF'
{
  "engineer": "Jordan Hale",
  "prd": "the PRD text",
  "change": "one sentence",
  "engineers_on_work": ["Jordan Hale", "Owen Briggs"],
  "placements": [
    {
      "verdict": "on",
      "okr": 1,
      "okr_line": "exact line from beef/goals.md",
      "stance": "for",
      "proposed_line": "goal text Accept would write"
    }
  ]
}
EOF
```

If the script rejects the JSON, fix the quote or the verdict and run it once more. Use the script's sentiment and opening. Do not invent counts.

## Reply

Short. Use this shape:

```text
Plan changed since your last call.
[only when the script prints that opening, plus who accepted it and which lines]

Request changes:
[only when the script prints a request-changes note for this engineer]

Change: one sentence.
Verdict: on OKR 1. Quote the goal line.
Engineers: who is already on that work, and what each one is building.
Sentiment: the script's for/against lines. One call does not move an OKR.
Goal line if accepted: the proposed line.
```

The reply does not change the goal. Say that in the sentiment line the script prints.
