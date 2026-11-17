# Decision memo template: automation investment

One page. Written so a sponsor can decide in ten minutes and a sceptic can find the weak point quickly.

## 1. Decision requested

*One sentence.* "Approve X to build and run Y for Z months."

## 2. Problem and baseline

- What work, how many items a month, who does it today, how long it takes, what it costs, current quality (first-pass yield).
- Source of each number (system report, time sample, estimate). Mark estimates as estimates.

## 3. Proposed solution

- What the automation does alone, what needs approval, what stays human (autonomy levels).
- Exception path and owner. Kill-switch owner.
- Governance tier and approver (see `ai-governance-framework`).

## 4. Economics

| Item | Base | Pessimistic | Optimistic |
|---|---|---|---|
| Build cost | | | |
| Monthly run cost (including model, review, exceptions) | | | |
| Volume per month | | | |
| Net minutes saved per task | | | |
| Realisation rate | | | |
| NPV over horizon | | | |
| Payback month | | | |

**Break-even volume:** ___ tasks per month. **Actual volume:** ___ (source).

## 5. What the saved capacity is for

Name where freed hours go (more volume with the same team, avoided hiring, quality work, new service). If the answer is "we will find something", the benefit is not real yet.

## 6. Risks and how they are controlled

| Risk | Likelihood | Impact | Control | Owner |
|---|---|---|---|---|

## 7. Pilot and success criteria

- Shadow mode for ___ weeks, then approval mode, then unattended only if criteria hold.
- Success: first-pass yield at least human baseline, override rate below ___, cost per task below ___.
- Stop rule: if ___ for two consecutive weeks, pause and review.

## 8. Ask and next step

Budget, people, date for the review.
