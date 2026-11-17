# Automation Business Case

Models for the two questions a director gets asked about every automation: **"Is it worth it?"** and **"How many people will we need?"**

- **ROI model:** build and run cost, benefit with a *realisation rate*, ramp-up, NPV, payback, break-even volume, and pessimistic, base and optimistic scenarios.
- **Forecasting:** demand forecasts (seasonal naive and Holt-Winters) judged by a rolling-origin backtest, so a model must beat the naive baseline before it is trusted.
- **Capacity and hiring:** forecast demand to required FTE (with utilisation target and shrinkage), then a hiring plan that accounts for lead time, ramp-up and attrition.

All numbers in the examples are synthetic. 29 tests, with expected values worked out by hand. Standard library only.

```bash
pip install -e .
bizcase                      # runs the worked example below
python -m unittest discover -s tests -v
```

## Worked example (synthetic)

An agent that checks briefs for completeness and routes requests: 1,800 tasks a month, saves 6 minutes of human time per task, but 1.5 minutes of review remain; people cost 14 per hour; build cost 12,000; run cost 450 a month.

```
NPV over 24 months: 5,691   payback month: 16
cost per task: 0.60   break-even volume: 612 tasks/month
  pessimistic  NPV    -15,147  payback None
  base         NPV      5,691  payback 16
  optimistic   NPV     17,785  payback 10
```

What a decision-maker should take from this, and what the model is built to expose:

1. **The base case is positive but not obviously a winner.** Payback at month 16 on a 24-month horizon is a modest case.
2. **The downside is real.** Volume 30% lower, realisation at 60% of plan and run cost 50% higher turns the NPV strongly negative. The decision hinges on volume and on whether saved time is genuinely reused.
3. **Break-even volume (612 a month) is the number to defend.** It is the one assumption sponsors can check against actual intake data.
4. **Review time is in the model.** Ignoring the 1.5 minutes of human review would overstate the net saving by a third (6 minutes instead of 4.5).

## Forecast and hiring (same synthetic series)

```
Forecast backtest (WAPE, lower is better)
  seasonal_naive 0.123   holt_winters 0.035
```

On a series with trend plus a Q4 peak, Holt-Winters cuts the error by about 70% against repeating last year's pattern, so it earns its complexity here. On a flat series it would not, and the backtest would show it.

The hiring plan starts hires **before** the gap opens, because lead time and ramp mean a hire started today lands later and contributes half-time at first.

## How the model avoids flattering itself

| Pitfall | Treatment |
|---|---|
| Counting every saved hour as cash | `realisation` rate (default 70%) scales benefits |
| Forgetting the human still in the loop | `review_minutes_per_task` is subtracted from savings |
| Instant full volume | Linear `ramp_months` |
| One optimistic number | Pessimistic, base and optimistic scenarios on realisation, volume and run cost |
| Ignoring time value | NPV with an annual discount rate |
| Trusting a fancy forecast | Must beat the seasonal-naive baseline in a rolling backtest |
| Plain 100% utilisation | Utilisation target and shrinkage (leave, training, sickness) |

## Layout

```
src/bizcase/
  roi.py       Initiative, cashflows, NPV, payback, scenarios, break-even
  forecast.py  seasonal naive, Holt-Winters, WAPE, backtest
  capacity.py  required FTE, hiring plan, utilisation
docs/          decision-memo template, assumptions register
```

## Limits

- Benefits here are labour-time based. Quality, speed, risk reduction and revenue effects need their own treatment and are best shown beside, not folded into, the NPV.
- Holt-Winters uses fixed smoothing parameters. Production use should fit them and quantify forecast intervals.
- The hiring plan is deterministic. A real plan would simulate demand and attrition variance.

## License

MIT
