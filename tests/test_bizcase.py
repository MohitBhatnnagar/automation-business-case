import math
import unittest

from bizcase import (CapacityModel, Initiative, backtest, breakeven_volume, cashflows, cost_per_task,
                     hiring_plan, holt_winters, monthly_benefit, net_minutes_per_task, npv,
                     payback_month, required_fte, scenarios, seasonal_naive, utilisation)
from bizcase.forecast import wape


def init(**kw):
    base = dict(name="x", build_cost=1000, monthly_run_cost=100, tasks_per_month=600,
                minutes_saved_per_task=5, review_minutes_per_task=1, loaded_hourly_cost=15,
                realisation=1.0, ramp_months=0, horizon_months=12, annual_discount_rate=0.0)
    base.update(kw)
    return Initiative(**base)


class RoiTests(unittest.TestCase):
    def test_net_minutes(self):
        self.assertEqual(net_minutes_per_task(init()), 4)

    def test_monthly_benefit_hand_computed(self):
        # 600 tasks * 4 min = 2400 min = 40 h * 15 = 600
        self.assertAlmostEqual(monthly_benefit(init(), 1), 600.0)

    def test_realisation_scales_benefit(self):
        self.assertAlmostEqual(monthly_benefit(init(realisation=0.5), 1), 300.0)

    def test_ramp_is_linear_then_flat(self):
        i = init(ramp_months=4)
        self.assertAlmostEqual(monthly_benefit(i, 1), 150.0)
        self.assertAlmostEqual(monthly_benefit(i, 4), 600.0)
        self.assertAlmostEqual(monthly_benefit(i, 9), 600.0)

    def test_cashflow_shape(self):
        cf = cashflows(init())
        self.assertEqual(len(cf), 13)
        self.assertEqual(cf[0], -1000)
        self.assertAlmostEqual(cf[1], 500.0)  # 600 benefit - 100 run

    def test_npv_without_discount_is_sum(self):
        self.assertAlmostEqual(npv(init()), -1000 + 12 * 500)

    def test_discounting_lowers_npv(self):
        self.assertLess(npv(init(annual_discount_rate=0.12)), npv(init()))

    def test_payback(self):
        self.assertEqual(payback_month(init()), 2)  # 500/month vs 1000 build
        self.assertIsNone(payback_month(init(tasks_per_month=10)))

    def test_cost_per_task(self):
        # run 100/600 + 1 min review at 15/h = 0.1667 + 0.25
        self.assertAlmostEqual(cost_per_task(init()), 100 / 600 + 0.25)

    def test_breakeven_volume(self):
        # per task: 4/60*15 = 1.0 ; run 100 -> 100 tasks
        self.assertAlmostEqual(breakeven_volume(init()), 100.0)

    def test_no_breakeven_when_review_eats_the_saving(self):
        with self.assertRaises(ValueError):
            breakeven_volume(init(minutes_saved_per_task=1, review_minutes_per_task=2))

    def test_scenarios_are_ordered(self):
        s = scenarios(init(annual_discount_rate=0.1))
        self.assertLess(s["pessimistic"]["npv"], s["base"]["npv"])
        self.assertLess(s["base"]["npv"], s["optimistic"]["npv"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            cashflows(init(realisation=1.5))
        with self.assertRaises(ValueError):
            cashflows(init(build_cost=-1))


class ForecastTests(unittest.TestCase):
    SEASON = [10, 20, 30, 20]

    def test_seasonal_naive_repeats_last_season(self):
        self.assertEqual(seasonal_naive(self.SEASON * 2, 6, 4), [10, 20, 30, 20, 10, 20])

    def test_holt_winters_recovers_pure_seasonality(self):
        fc = holt_winters(self.SEASON * 4, 4, 4)
        for a, b in zip(fc, self.SEASON):
            self.assertAlmostEqual(a, b, places=6)

    def test_holt_winters_follows_a_trend(self):
        series = [100 + 2 * t + (10 if t % 4 == 0 else 0) for t in range(24)]
        fc = holt_winters(series, 4, 4)
        actual = [100 + 2 * t + (10 if t % 4 == 0 else 0) for t in range(24, 28)]
        self.assertLess(wape(actual, fc), 0.03)

    def test_needs_two_seasons(self):
        with self.assertRaises(ValueError):
            holt_winters([1, 2, 3, 4, 5], 2, 4)

    def test_wape_hand_computed(self):
        self.assertAlmostEqual(wape([100, 0, 100], [90, 10, 110]), 30 / 200)

    def test_wape_rejects_zero_actuals(self):
        with self.assertRaises(ValueError):
            wape([0, 0], [1, 1])

    def test_backtest_prefers_holt_winters_on_trending_series(self):
        series = [100 + 3 * t + (15 if t % 6 in (4, 5) else 0) for t in range(48)]
        r = backtest(series, season=6)
        self.assertLess(r["holt_winters"], r["seasonal_naive"])

    def test_backtest_short_series(self):
        with self.assertRaises(ValueError):
            backtest([1.0] * 5, season=4)


class CapacityTests(unittest.TestCase):
    M = CapacityModel(minutes_per_unit=60, hours_per_fte_month=160, target_utilisation=0.8, shrinkage=0.0)

    def test_required_fte_hand_computed(self):
        # 640 units * 1 h = 640 h ; 160 * 0.8 = 128 productive h per FTE -> 5 FTE
        self.assertAlmostEqual(required_fte(640, self.M), 5.0)

    def test_shrinkage_raises_requirement(self):
        m = CapacityModel(60, 160, 0.8, 0.2)
        self.assertGreater(required_fte(640, m), required_fte(640, self.M))

    def test_utilisation(self):
        self.assertAlmostEqual(utilisation(640, 5, self.M), 640 / (5 * 160))

    def test_model_validation(self):
        with self.assertRaises(ValueError):
            required_fte(10, CapacityModel(60, 160, 1.5))

    def test_flat_demand_no_hiring(self):
        plan = hiring_plan([640] * 6, current_fte=5.0, m=self.M, monthly_attrition=0.0)
        self.assertTrue(all(r["start_hiring"] == 0 for r in plan))

    def test_growth_triggers_hiring_before_the_gap(self):
        demand = [640, 640, 640, 640, 1280, 1280, 1280, 1280]
        plan = hiring_plan(demand, current_fte=5.0, m=self.M, monthly_attrition=0.0, lead_time_months=2)
        # demand doubles in month 5; hiring must START by month 3
        started = [r["month"] for r in plan if r["start_hiring"]]
        self.assertEqual(started[0], 3)
        self.assertEqual(plan[2]["start_hiring"], 5)

    def test_attrition_causes_replacement_hiring(self):
        plan = hiring_plan([640] * 12, current_fte=5.0, m=self.M, monthly_attrition=0.05, lead_time_months=2)
        self.assertGreater(sum(r["start_hiring"] for r in plan), 0)

    def test_attrition_validation(self):
        with self.assertRaises(ValueError):
            hiring_plan([1], 1, self.M, monthly_attrition=1.0)


if __name__ == "__main__":
    unittest.main()
