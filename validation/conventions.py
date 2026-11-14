"""Pure acceptance examples, not a backtest engine or production calendar."""
from calendar import monthrange
from datetime import date
from math import isfinite
from .ledger import IntegrityError, require, timestamp


def schedule(values):
    """Caller supplies authenticated ordered official session closing instants."""
    result = [timestamp(v) for v in values]
    require(bool(result) and all(a < b for a, b in zip(result, result[1:])), "unordered/duplicate calendar")
    require(len({v.date() for v in result}) == len(result), "multiple closes per date")
    return result


def reference_close(available_at, closes):
    if available_at is None:
        return None
    available = timestamp(available_at)
    return next((v for v in schedule(closes) if v > available), None)


def daily_endpoint(entry, intervals, closes):
    require(intervals in {5, 10, 20}, "undeclared daily horizon")
    values = schedule(closes)
    require(entry in values, "entry absent from official schedule")
    index = values.index(entry) + intervals
    return values[index] if index < len(values) else None


def weekly_endpoint(entry_date, months, closes):
    require(months in {3, 6}, "undeclared weekly horizon")
    year, month = divmod(entry_date.year * 12 + entry_date.month - 1 + months, 12)
    month += 1
    target = date(year, month, min(entry_date.day, monthrange(year, month)[1]))
    return target, next((v for v in schedule(closes) if v.date() >= target), None)


def volume_state(volumes):
    require(len(volumes) == 60, "weekly gate requires exactly preceding 60 scheduled sessions")
    require(all(v is None or (isfinite(v) and v >= 0) for v in volumes), "invalid volume")
    # Both states remain visible; missing never becomes an explicit zero.
    return {"zero_sessions": sum(v == 0 for v in volumes), "missing_sessions": sum(v is None for v in volumes),
            "status": "fails_zero_trade" if 0 in volumes else "unverified" if None in volumes else "verified_positive_sessions",
            "capacity": "unverified"}


def buy_net(gross, entry_cost, exit_cost):
    require(all(isfinite(v) for v in (gross, entry_cost, exit_cost)) and gross >= -1 and 0 <= entry_cost < 1 and 0 <= exit_cost < 1, "invalid return/cost")
    return (1 + gross) * (1 - exit_cost) / (1 + entry_cost) - 1


def sell_avoided(holding_return, sale_cost):
    require(isfinite(holding_return) and holding_return >= -1 and isfinite(sale_cost) and 0 <= sale_cost < 1, "invalid holding/cost")
    return -holding_return - sale_cost


def outcome_state(*, suspended=False, delisted=False, consideration=None):
    """No outcome prices calculated or last-price/cash-zero substitute created."""
    if suspended or delisted:
        return "unresolved" if consideration is None else "requires_consideration_audit"
    return "not_collected"
