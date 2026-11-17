"""Demand forecasting: seasonal naive baseline and Holt-Winters (additive), with backtests.

A forecast is only worth using if it beats the naive baseline out of sample, so the
backtest compares models on rolling origins and reports WAPE.
"""
from __future__ import annotations


def seasonal_naive(history: list[float], horizon: int, season: int) -> list[float]:
    if len(history) < season:
        raise ValueError("need at least one full season of history")
    return [history[len(history) - season + (h % season)] for h in range(horizon)]


def holt_winters(history: list[float], horizon: int, season: int,
                 alpha: float = 0.4, beta: float = 0.1, gamma: float = 0.3) -> list[float]:
    """Additive Holt-Winters. Needs at least two seasons to initialise level, trend and seasonals."""
    n = len(history)
    if season < 2 or n < 2 * season:
        raise ValueError("need at least two full seasons of history")
    if not all(0 <= p <= 1 for p in (alpha, beta, gamma)):
        raise ValueError("smoothing parameters must be between 0 and 1")
    first, second = history[:season], history[season:2 * season]
    level = sum(first) / season
    trend = (sum(second) - sum(first)) / season / season
    seas = [x - level for x in first]
    for t in range(season, n):
        x, s = history[t], seas[t % season]
        prev_level = level
        level = alpha * (x - s) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seas[t % season] = gamma * (x - level) + (1 - gamma) * s
    return [level + (h + 1) * trend + seas[(n + h) % season] for h in range(horizon)]


def wape(actual: list[float], forecast: list[float]) -> float:
    """Weighted absolute percentage error: sum|a - f| / sum|a|. Safe when some actuals are 0."""
    if len(actual) != len(forecast) or not actual:
        raise ValueError("need equal-length, non-empty series")
    total = sum(abs(a) for a in actual)
    if total == 0:
        raise ValueError("actuals sum to zero")
    return sum(abs(a - f) for a, f in zip(actual, forecast)) / total


def backtest(series: list[float], season: int, horizon: int = 3, min_train: int | None = None) -> dict[str, float]:
    """Rolling-origin evaluation: forecast `horizon` steps from each origin, average the error."""
    start = min_train or 2 * season
    errs: dict[str, list[float]] = {"seasonal_naive": [], "holt_winters": []}
    for origin in range(start, len(series) - horizon + 1):
        train, actual = series[:origin], series[origin:origin + horizon]
        errs["seasonal_naive"].append(wape(actual, seasonal_naive(train, horizon, season)))
        errs["holt_winters"].append(wape(actual, holt_winters(train, horizon, season)))
    if not errs["holt_winters"]:
        raise ValueError("series too short to backtest")
    return {k: sum(v) / len(v) for k, v in errs.items()}
