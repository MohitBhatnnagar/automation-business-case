"""Business case for an automation: cost, benefit, NPV, payback and sensitivity.

Honest by construction: benefits are discounted by a *realisation rate* (not every saved
hour becomes cash or capacity), run costs include the human review that stays in the loop,
and the case is shown across scenarios rather than as one flattering number.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Initiative:
    name: str
    build_cost: float                 # one-off: design, build, testing, change management
    monthly_run_cost: float           # licences, model usage, hosting, maintenance
    tasks_per_month: float            # volume handled
    minutes_saved_per_task: float     # gross human time removed per task
    review_minutes_per_task: float    # human time still spent reviewing or handling exceptions
    loaded_hourly_cost: float         # fully loaded cost of the people time involved
    realisation: float = 0.7          # share of net saved time that becomes real value (0-1)
    ramp_months: int = 3              # months to reach full volume (linear ramp)
    horizon_months: int = 24
    annual_discount_rate: float = 0.10

    def validate(self) -> None:
        if min(self.build_cost, self.monthly_run_cost, self.tasks_per_month,
               self.minutes_saved_per_task, self.review_minutes_per_task, self.loaded_hourly_cost) < 0:
            raise ValueError("costs, volumes and times cannot be negative")
        if not 0 <= self.realisation <= 1:
            raise ValueError("realisation must be between 0 and 1")
        if self.horizon_months < 1 or self.ramp_months < 0:
            raise ValueError("horizon must be >= 1 and ramp >= 0")
        if self.annual_discount_rate < 0:
            raise ValueError("discount rate cannot be negative")


def net_minutes_per_task(i: Initiative) -> float:
    return i.minutes_saved_per_task - i.review_minutes_per_task


def monthly_benefit(i: Initiative, month: int) -> float:
    """Benefit in a given month (1-based), with a linear ramp to full volume."""
    ramp = 1.0 if i.ramp_months == 0 else min(1.0, month / i.ramp_months)
    hours = i.tasks_per_month * ramp * net_minutes_per_task(i) / 60
    return hours * i.loaded_hourly_cost * i.realisation


def cashflows(i: Initiative) -> list[float]:
    """Index 0 is the build cost (month 0); then net benefit minus run cost per month."""
    i.validate()
    return [-i.build_cost] + [monthly_benefit(i, m) - i.monthly_run_cost for m in range(1, i.horizon_months + 1)]


def npv(i: Initiative) -> float:
    r = (1 + i.annual_discount_rate) ** (1 / 12) - 1  # equivalent monthly rate
    return sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows(i)))


def payback_month(i: Initiative) -> int | None:
    """First month in which cumulative (undiscounted) cash turns non-negative, else None."""
    total = 0.0
    for t, cf in enumerate(cashflows(i)):
        total += cf
        if t > 0 and total >= 0:
            return t
    return None


def cost_per_task(i: Initiative) -> float:
    """Steady-state cost per task: run cost plus review time, versus the manual baseline."""
    review = i.review_minutes_per_task / 60 * i.loaded_hourly_cost
    return i.monthly_run_cost / i.tasks_per_month + review


def scenarios(i: Initiative) -> dict[str, dict]:
    """Pessimistic, base and optimistic on the assumptions that are usually wrong:
    realisation, volume and run cost."""
    cases = {
        "pessimistic": replace(i, realisation=i.realisation * 0.6, tasks_per_month=i.tasks_per_month * 0.7,
                               monthly_run_cost=i.monthly_run_cost * 1.5),
        "base": i,
        "optimistic": replace(i, realisation=min(1.0, i.realisation * 1.2), tasks_per_month=i.tasks_per_month * 1.2),
    }
    return {k: {"npv": round(npv(v), 2), "payback_month": payback_month(v)} for k, v in cases.items()}


def breakeven_volume(i: Initiative) -> float:
    """Tasks per month needed for steady-state benefit to cover the run cost (ignores build cost)."""
    per_task = net_minutes_per_task(i) / 60 * i.loaded_hourly_cost * i.realisation
    if per_task <= 0:
        raise ValueError("net saving per task is not positive: this automation cannot break even")
    return i.monthly_run_cost / per_task
