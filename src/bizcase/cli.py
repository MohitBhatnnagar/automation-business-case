"""Demo: business case, forecast backtest and hiring plan on synthetic numbers."""
from __future__ import annotations

import sys

from .capacity import CapacityModel, hiring_plan
from .forecast import backtest, holt_winters
from .roi import Initiative, breakeven_volume, cost_per_task, npv, payback_month, scenarios


def main(argv: list[str] | None = None) -> int:
    i = Initiative("Automated brief check and routing", build_cost=12000, monthly_run_cost=450,
                   tasks_per_month=1800, minutes_saved_per_task=6, review_minutes_per_task=1.5,
                   loaded_hourly_cost=14)
    print(f"== {i.name}")
    print(f"NPV over {i.horizon_months} months: {npv(i):,.0f}   payback month: {payback_month(i)}")
    print(f"cost per task: {cost_per_task(i):.2f}   break-even volume: {breakeven_volume(i):,.0f} tasks/month")
    for k, v in scenarios(i).items():
        print(f"  {k:<12} NPV {v['npv']:>10,.0f}  payback {v['payback_month']}")

    demand = [800 + 12 * t + (120 if t % 12 in (9, 10, 11) else 0) for t in range(36)]  # trend + Q4 peak
    print("\n== Forecast backtest (WAPE, lower is better)", backtest(demand, season=12))
    fc = holt_winters(demand, 6, 12)
    m = CapacityModel(minutes_per_unit=95)
    print("\n== Hiring plan (next 6 months)")
    for row in hiring_plan(fc, current_fte=15.0, m=m):
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
