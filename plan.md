# Chief and Chief Brief

Two parts. Engineers use Chief. The CEO and the CPO use Chief Brief.

**Chief.** An engineer types `/chief` in Grok, then a PRD. Chief reads that PRD and answers that engineer: what other engineers are already building, and whether the PRD sits on the OKRs. Sentiment is the recent `/chief` calls, counted for and against.

**Chief Brief.** The CEO and the CPO type `/brief` in Grok. That opens the Chief Brief website. The page gathers the `/chief` calls into one view of what the engineers are doing, and whether that work is still on the OKRs. It looks like a pull request. Accepting it updates the plan. The next `/chief` call uses that plan.

## Problem

A PRD can be sound for one team and still move the company off its OKRs. The CEO and the CPO also have no single view of what each engineer is doing this week. Chief is the check for the engineer. Chief Brief is the view for the CEO and the CPO.

## What `/chief` does

Input is one PRD.

1. Name the change the PRD asks for, in one sentence.
2. Find the engineers already on nearby work, and read their latest calls.
3. Place the PRD on an OKR: on it, beside it, or in conflict with it.

The reply is short:

- Verdict: on the OKR, beside it, or in conflict.
- The OKR line it touches.
- The engineers on that work, and what each one is building.
- Sentiment: how many calls agree, and how many do not. One call is not enough to move an OKR.
- The plan line that would change if leadership accepted it.

That reply stays with the engineer. It does not change the plan. The CEO and the CPO change the plan from Chief Brief. Until they accept, the next `/chief` still uses the old OKRs.

## Two outcomes

**What engineers are doing.** Each engineer has a current piece of work, the OKR it serves, and a last call. When Chief reviews a PRD, it shows the people already on that work so the overlap is visible before the argument.

**OKR alignment.** The OKRs are the plan. Chief says which OKR the PRD serves, and quotes the line. A PRD that fights a line is a conflict, even if the engineers writing it want it.

## Current OKRs

1. Grow treated patients 20% by opening one new trial site. The site opens in November. Added patients run through Q1.
2. Months of supply stay at or above 3.
3. Runway stays at or above 12 months. It is 14 months today. Opening the site in November puts it at 11.

## Seed batch

Five engineers. Faces are generated images from [thispersondoesnotexist.com](https://thispersondoesnotexist.com/), saved once so the face stays with the name. They are not real people.

### Nate Adler

<img src="public/avatars/nate.jpg" alt="Nate Adler" width="96" />

Lab platform. Wrapping Primer3 so an agent can design primers without a person at the terminal. Serves OKR 1 from the side: scientists stay on the trial. Last call: build it. It does not change the site plan.

### Jordan Hale

<img src="public/avatars/jordan.jpg" alt="Jordan Hale" width="96" />

Supply. Dose demand for the new trial site. On OKR 1, watching OKR 2. Last call: open the site in November. Supply covers the added patients through Q1. A second site this quarter does not.

### Owen Briggs

<img src="public/avatars/owen.jpg" alt="Owen Briggs" width="96" />

Clinical data. Enrollment against the October plan. On OKR 1. Last call: enrollment is on the October plan. Do not add a second site this quarter.

### Sam Pell

<img src="public/avatars/sam.jpg" alt="Sam Pell" width="96" />

Finance systems. Burn and runway. On OKR 3. Last call: runway is 14 months at the current burn, and 11 months if the site opens in November. That misses OKR 3.

### Alex Ruiz

<img src="public/avatars/alex.jpg" alt="Alex Ruiz" width="96" />

Cold chain. Months of supply at the treatment sites. On OKR 2. Last call: hold a new site if months of supply would fall under 3. November still clears that line.

## Worked example

PRD: "Open the new trial site in November and let agents run Primer3."

Chief would answer:

- On OKR 1 for the site. Beside OKR 1 for Primer3. In conflict with OKR 3, because runway falls to 11 months.
- Engineers: Jordan and Owen on the site, Nate on Primer3, Sam on the runway number, Alex on supply.
- Sentiment: 2 calls to open in November (Jordan, Alex says supply still clears). 1 call against a second site (Owen). 1 call that the runway miss is real (Sam). 1 call for Primer3 (Nate).
- Plan edit, if the CEO and the CPO accept it on Chief Brief: replace "Hold the new site until months of supply stay above 3" with "Open the new site in November. Supply covers the added patients through Q1." Add "Let lab agents run Primer3." Replace "Runway is 14 months at the current burn" with "Runway is 11 months if the new site opens in November."

## Chief Brief

For the CEO and the CPO. They type `/brief` in Grok, and Grok opens the website. The website is a page, not a git pull request. It looks like one.

- Title, open state, and a one-line count of `/chief` calls.
- What the engineers are doing, grouped into themes, including work that does not fit the plan.
- `Priorities` and `Performance` as a side-by-side diff. Removals on the left, additions on the right. Unchanged lines on both sides.
- Each changed line cites the engineers behind it.
- Accept, request changes, or decline. Accept republishes the plan. The next `/chief` in Grok uses that plan.

## Out of scope

Live warehouse numbers inside the brief. Any engineer outside this batch of five.

## CEO context pipeline

Helen’s mailbox and calendar are ingested for this loop. Agents: read [docs/data-ingestion.md](docs/data-ingestion.md). Snapshots will live under `data/`. The morning job writes [briefs/pending.md](briefs/pending.md) and **must** start from the last review in [briefs/REVIEW.md](briefs/REVIEW.md). It never Accepts. `/chief` still reads **Current OKRs** above until a Brief Accept republishes them.
