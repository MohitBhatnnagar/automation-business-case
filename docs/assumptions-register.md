# Assumptions register

Every number in a business case is an assumption until it is measured. Keep them in one table, with an owner and a date to verify. Review it whenever the case is revisited.

| # | Assumption | Value | Evidence | Confidence | How to verify | Owner | Check by |
|---|---|---|---|---|---|---|---|
| 1 | Tasks per month | | | High / Med / Low | Intake system report, last 6 months | | |
| 2 | Minutes per task today | | | | Time sample of 30 tasks | | |
| 3 | Minutes removed by automation | | | | Shadow-mode comparison | | |
| 4 | Review minutes per task remaining | | | | Reviewer time log | | |
| 5 | Realisation rate | | | | Where did the saved hours go? | | |
| 6 | Loaded hourly cost | | | | Finance | | |
| 7 | Monthly run cost | | | | Vendor invoices, usage logs | | |
| 8 | Ramp-up period | | | | Pilot adoption curve | | |

## Sensitivity: which assumption matters most?

Change each assumption by 20% and record the NPV movement. The top two are where to spend verification effort. The `scenarios()` function in `roi.py` already stresses realisation, volume and run cost together; a one-at-a-time sensitivity is the natural next step.

## Tripwires

Pre-agree the values at which the case no longer holds (for example volume below break-even for two consecutive months), and who is told when that happens.
