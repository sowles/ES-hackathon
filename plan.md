# Chief, Chief Beef, and Chief Brief

Engineers use Chief. Data pipelines keep Chief Beef current. The CEO and the CPO read Chief Brief, and the only thing they change is the goal inside Chief Beef.

**Chief.** An engineer types `/chief` in Grok, then a PRD. Chief reads that PRD and answers that engineer: what other engineers are already building, and whether the PRD sits on the OKRs. Sentiment is the recent `/chief` calls, counted for and against.

**Chief Beef.** The company context plus the goal. Pipelines update it all the time. The context is the inflow: Slack chats, git merges, Helen's mail and calendar, and the `/chief` calls. The goal is the OKRs, each with a time horizon. The pipelines keep the context coupled to that goal.

**Chief Brief.** Compiled automatically from Chief Beef. No person writes it. The CEO and the CPO type `/brief` in Grok, and that opens the latest compilation. The page shows what the engineers are doing, and whether that work is still on the OKRs. It looks like a pull request. Accepting it writes the proposed change into the goal of Chief Beef. The next brief compiles itself from that beef, and the next `/chief` call reads that goal.

## The metaphor, all the way down

Chief treats the company plan as a repository and engineering work as commits against it. Every Git idea the brief uses means one thing a CEO can act on:

| Git idea | In Chief Brief | The question it answers |
| --- | --- | --- |
| diff | Priorities and Performance, removals left, additions right | What changed in the plan? |
| blame | Click any OKR line to see the calls and engineers that moved it | Why did this line change? |
| merge conflict | Two engineers building overlapping or contradictory work | Who is about to duplicate or collide? |
| branch | Work that sits beside an OKR or on none | What is being built that nobody approved? |
| history | Every accepted version of the plan, with who accepted it | How many times has this moved? |

## Problem

A PRD can be sound for one team and still move the company off its OKRs. The CEO and the CPO also have no single view of what each engineer is doing this week. Chief is the check for the engineer. Chief Brief is the view for the CEO and the CPO.

## What `/chief` does

Input is one PRD.

1. Name the change the PRD asks for, in one sentence.
2. Find the engineers already on nearby work, and read their latest calls.
3. Place the PRD on an OKR: on it, beside it, in conflict with it, or unclassified when Chief cannot match it to any OKR line with confidence. Chief never forces a weak match.

The reply is short:

- Verdict: on the OKR, beside it, in conflict, or unclassified.
- The OKR line it touches.
- The engineers on that work, and what each one is building.
- Sentiment: how many calls agree, and how many do not. One call is not enough to move an OKR.
- The plan line that would change if leadership accepted it.
- Plan changed since your last call. If the CEO and the CPO accepted a Brief after this engineer's previous `/chief`, the reply opens with the lines that changed and who accepted them. Alignment runs both directions: leadership sees engineering, and engineers see leadership's decisions.

That reply stays with the engineer. It does not change the goal. The CEO and the CPO change the goal by accepting a brief. Until they accept, the next `/chief` still uses the old goal.

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

Supply. Dose demand for the new trial site. On OKR 1, watching OKR 2. Last call: open the site in November. Supply covers the added patients through Q1. A second site this quarter does not. Jordan is also building a months-of-supply forecast for the new site.

### Owen Briggs

<img src="public/avatars/owen.jpg" alt="Owen Briggs" width="96" />

Clinical data. Enrollment against the October plan. On OKR 1. Last call: enrollment is on the October plan. Do not add a second site this quarter.

### Sam Pell

<img src="public/avatars/sam.jpg" alt="Sam Pell" width="96" />

Finance systems. Burn and runway. On OKR 3. Last call: runway is 14 months at the current burn, and 11 months if the site opens in November. That misses OKR 3.

### Alex Ruiz

<img src="public/avatars/alex.jpg" alt="Alex Ruiz" width="96" />

Cold chain. Months of supply at the treatment sites. On OKR 2. Last call: hold a new site if months of supply would fall under 3. November still clears that line. Alex's months-of-supply model already covers the new site, so Jordan's forecast duplicates it.

## Worked example

PRD: "Open the new trial site in November and let agents run Primer3."

Chief would answer:

- On OKR 1 for the site. Beside OKR 1 for Primer3. In conflict with OKR 3, because runway falls to 11 months.
- Engineers: Jordan and Owen on the site, Nate on Primer3, Sam on the runway number, Alex on supply.
- Sentiment: 2 calls to open in November (Jordan, Alex says supply still clears). 1 call against a second site (Owen). 1 call that the runway miss is real (Sam). 1 call for Primer3 (Nate).
- Goal edit, if the CEO and the CPO accept it: replace "Hold the new site until months of supply stay above 3" with "Open the new site in November. Supply covers the added patients through Q1." Add "Let lab agents run Primer3." Replace "Runway is 14 months at the current burn" with "Runway is 11 months if the new site opens in November." That write lands on the goal of Chief Beef. The brief recompiles from there.
- Overlap: Jordan and Alex are both forecasting months of supply for the new site.

## Chief Beef

Chief Beef is the company context plus the goal. Data pipelines update it all the time. No person maintains it. The CEO and the CPO read the brief compiled from it, and the only thing they alter is the goal.

**The goal.** The OKRs, each with a time horizon. A line is a target and a window. From the current plan: the new site opens in November, the added patients run through Q1, months of supply stay at or above 3, runway stays at or above 12 months. Work inside the window can move the line. Work past the window, or with no window, does not. Accept on a brief is the only way this side changes.

**The context.** A constant inflow from the pipelines. Slack chats, git merges, Helen's mail and calendar, and the `/chief` calls. Each item arrives with a person and a time. The pipelines keep writing it. Nobody edits a chat, a merge, or a call by hand.

**The coupling.** A Slack thread or a merged change matters when it supports, fights, or sits beside a goal inside that goal's window. Chief Beef keeps the pair: what arrived, and the OKR line and window it touches. Inflow that matches no line stays unclassified. The same rule `/chief` uses. A weak match is never forced.

## Chief Brief

Compiled automatically from Chief Beef whenever the beef changes. No person writes the page. The CEO and the CPO type `/brief` in Grok, and Grok opens the latest compilation. The website is a page, not a git pull request. It looks like one. Accept writes the proposed lines into the goal of Chief Beef and leaves the context alone. Request changes and Decline leave the goal as it is.

Top to bottom:

1. Title, open state, and a one-line count of `/chief` calls.
2. Decisions needed. At most three items blocked on the CEO or the CPO, each with the one-click answers it needs. Example: "Runway falls to 11 months under OKR 3's floor of 12. Accept the miss, or ask Sam for a burn offset?"
3. Effort by OKR (say versus do). One bar per OKR showing how many engineers' current work sits on it, plus a bar for work on no OKR. Example from the seed batch: OKR 1 has 3, OKR 2 has 1, OKR 3 has 1, beside or none has 1 (Nate). The gap between what leadership says matters and where engineering time goes is visible in one glance.
4. What the engineers are doing, grouped into themes, including work that does not fit the plan. Work beside an OKR or on none is labeled a branch, with two buttons: promote to plan or pause.
5. Merge conflicts. Pairs of engineers building overlapping or contradictory work, found by comparing their current work and last calls. Example: Jordan and Alex both forecasting months of supply for the new site.
6. Priorities and Performance as a side-by-side diff. Removals on the left, additions on the right. Unchanged lines on both sides.
7. Each changed line cites the engineers behind it. Clicking any line opens blame: the PRD, the `/chief` calls, and the sentiment count that produced the change, in order.
8. Accept, request changes, or decline. Accept writes the proposed lines into the goal of Chief Beef. The brief recompiles from that beef. The next `/chief` in Grok reads that goal. Request changes and Decline do not alter the beef.
9. Request changes takes a comment. The comment goes to every engineer cited on that line, through Slack, and opens their next `/chief` reply.
10. History. Every accepted version of the plan is kept with who accepted it and when, so the brief can show "this line has moved 3 times."

## Demo (three minutes)

One story, every step visible, the problem solved by the end.

1. Open. The CEO types `/brief`. Decisions needed shows one item: OKR 3 is off track, runway 11 months against a floor of 12.
2. Blame. The CEO clicks the OKR 3 line. Blame shows the PRD to open the site in November, Jordan's and Alex's calls for it, and Sam's call that the runway miss is real.
3. Merge conflict. The brief shows Jordan and Alex both forecasting months of supply for the new site.
4. Resolve with one comment. The CEO clicks Request changes on the site line: "Open in November. Sam, bring a burn offset that keeps runway at 12 or more. Alex owns the supply forecast; Jordan, drop the duplicate." The comment lands in Slack for Sam, Alex and Jordan.
5. Close the loop. Jordan runs `/chief` on a new PRD. The reply opens with "Plan changed since your last call" and the CEO's decision.

## Out of scope

Live warehouse numbers inside the brief. Any engineer outside this batch of five.

## CEO context pipeline

Data pipelines update Chief Beef all the time. The context inflow is Helen's mailbox and calendar, Slack chats, git merges, and the `/chief` calls, each kept with the person, the time, and the OKR window it touches. Agents: read `docs/data-ingestion.md`. Snapshots will live under `data/`. The compiler reads Chief Beef and writes the brief to `briefs/pending.md`. It starts from the last review in `briefs/REVIEW.md`. It never changes the goal. Only an Accept from the CEO or the CPO does that. `/chief` still reads the goal in Current OKRs above until that Accept.
