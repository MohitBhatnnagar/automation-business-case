"""Turn a demand forecast into required headcount and a hiring plan."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityModel:
    minutes_per_unit: float            # handling time per work item
    hours_per_fte_month: float = 160.0
    target_utilisation: float = 0.80   # leave slack for reviews, training, leave, variance
    shrinkage: float = 0.12            # leave, sickness, training: share of paid time unavailable

    def validate(self) -> None:
        if self.minutes_per_unit <= 0 or self.hours_per_fte_month <= 0:
            raise ValueError("handling time and hours must be positive")
        if not 0 < self.target_utilisation <= 1:
            raise ValueError("target utilisation must be in (0, 1]")
        if not 0 <= self.shrinkage < 1:
            raise ValueError("shrinkage must be in [0, 1)")


def required_fte(demand_units: float, m: CapacityModel) -> float:
    m.validate()
    work_hours = demand_units * m.minutes_per_unit / 60
    productive_hours_per_fte = m.hours_per_fte_month * (1 - m.shrinkage) * m.target_utilisation
    return work_hours / productive_hours_per_fte


def hiring_plan(forecast: list[float], current_fte: float, m: CapacityModel,
                monthly_attrition: float = 0.01, lead_time_months: int = 2,
                ramp_productivity: float = 0.5) -> list[dict]:
    """Month-by-month gap and the hires to START now so they land after the lead time.

    A hire started in month t is productive from month t + lead_time at `ramp_productivity`
    of an experienced person (first month), then fully. Attrition reduces headcount monthly.
    """
    if not 0 <= monthly_attrition < 1:
        raise ValueError("attrition must be in [0, 1)")
    plan, fte = [], current_fte
    pending: dict[int, float] = {}
    for month, demand in enumerate(forecast, start=1):
        fte = fte * (1 - monthly_attrition) + pending.pop(month, 0.0)
        need = required_fte(demand, m)
        gap = need - fte
        # decide hires for the month when they will matter
        land = month + lead_time_months
        if land <= len(forecast):
            future_need = required_fte(forecast[land - 1], m)
            projected = fte * (1 - monthly_attrition) ** lead_time_months + sum(
                v for k, v in pending.items() if k <= land)
            hire = max(0, math.ceil(future_need - projected - 1e-9))
            if hire:
                pending[land] = pending.get(land, 0.0) + hire * ramp_productivity
                pending[land + 1] = pending.get(land + 1, 0.0) + hire * (1 - ramp_productivity)
        else:
            hire = 0
        plan.append({"month": month, "demand": round(demand), "required_fte": round(need, 1),
                     "available_fte": round(fte, 1), "gap_fte": round(gap, 1), "start_hiring": hire})
    return plan


def utilisation(demand_units: float, fte: float, m: CapacityModel) -> float:
    """Share of productive time consumed. Above target means burnout and queues."""
    m.validate()
    if fte <= 0:
        raise ValueError("fte must be positive")
    work_hours = demand_units * m.minutes_per_unit / 60
    return work_hours / (fte * m.hours_per_fte_month * (1 - m.shrinkage))
