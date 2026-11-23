"""MCP server for the dual-risk DCF calculations.

Runs on the user's own machine over stdio. It computes from the numbers it is
given and nothing else: no network access, no stored data, no forecasts.

    python -m dualrisk.server
"""
from __future__ import annotations

import functools

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import core

NOTE = ("Computed with the formulas of the cited article from the inputs given. "
        "It describes those inputs; it is not a forecast or a recommendation.")

mcp = MCPServer(
    "dual-risk-dcf",
    instructions=(
        "Calculations of the dual-risk DCF framework: a valuation is split into a benchmark "
        "cost of capital c and a valuation ratio K = V_fair / V. Rates are decimals (0.08 for "
        "8%) per period, a year unless stated. Benefit streams are lists of [time, amount] with "
        "time > 0 counted in periods. K > 1 means the valuation or price is below the benchmark "
        "fair value; K < 1 means it is above. Source: " + core.CITATION),
)


REGISTRY: list[tuple[str, str]] = []   # (tool name, first line of its description), for the guide


def tool(fn):
    """Register a tool. An input the formulas are not defined for is reported
    to the caller in words instead of as a crash."""
    @functools.wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
    REGISTRY.append((fn.__name__, fn.__doc__.strip().splitlines()[0]))
    return mcp.tool()(run)


def _out(result: dict) -> dict:
    return {**result, "source": core.CITATION, "note": NOTE}


@tool
def compare_forecasts(c: float, benchmark: list[list[float]], own: list[list[float]]) -> dict:
    """Split the gap between two forecasts of the same asset into c and K.

    `benchmark` is the reference (unbiased) forecast and `own` the forecast being examined, each a
    list of [time, expected benefit]. Both are discounted at the benchmark rate `c`. Returns the two
    present values, K, the gain of capital g = (1+c)^h (K-1), and the effective rate c_eff: the single
    rate that would make `own` worth the benchmark value. `c_eff` is the article's closed form;
    `c_eff_stream` solves the general definition and differs from it when benefits arrive over time.
    """
    return _out(core.from_forecasts(c, benchmark, own))


@tool
def compare_with_price(c: float, benchmark: list[list[float]], price: float) -> dict:
    """Set a forecast against an observed price.

    The forecast, a list of [time, expected benefit], is discounted at `c` to give the fair value;
    the price stands in for the valuation. Returns K = fair value / price, the gain of capital, the
    expected return per period if the forecast is right, (1+c) K^(1/h) - 1, and c_eff.
    """
    return _out(core.against_price(c, benchmark, price))


@tool
def perpetuity(c: float, growth: float, benefit_fair: float, benefit_own: float) -> dict:
    """Constant-growth (Gordon) case: same growth under both beliefs, different first-period benefit.

    Returns both values, K, the value wedge and c_eff = (c - growth) / K + growth.
    """
    return _out(core.perpetuity(c, growth, benefit_fair, benefit_own))


@tool
def convert(c: float, horizon: float, K: float | None = None, gain: float | None = None) -> dict:
    """Convert between K and the gain of capital g at a given c and horizon, and give c_eff.

    Give exactly one of `K` or `gain`.
    """
    if (K is None) == (gain is None):
        raise ValueError("give exactly one of K or gain")
    if K is None:
        K = core.ratio_from_gain(c, gain, horizon)
    return _out({"c": c, "horizon": horizon, "K": K, "gain": core.gain_of_capital(c, K, horizon),
                 "c_eff": core.effective_rate(c, K, horizon)})


@tool
def market_clearing_price(v_fair: float, ratios: list[float], weights: list[float] | None = None,
                          supply: float = 1.0, depth: float = 1.0) -> dict:
    """Price that clears a market of agents who each value the asset at v_fair / K_i.

    Linear demand with depth `depth` (lambda) and net supply `supply` (Q):
    P = v_fair * mean(1/K) - Q / lambda. `weights` are the shares of agents at each K.
    """
    return _out(core.clearing_price(v_fair, ratios, weights, supply, depth))


@tool
def price_history(prices: list[float], periods_per_year: int = 52, horizon_periods: int | None = None,
                  c: float | None = None, window_periods: int | None = None, floor: float = 0.03,
                  include_rows: bool = False) -> dict:
    """Run the article's back-test on a series of total-return prices, oldest first.

    For each date with a price one horizon later it gives c_t, the realized valuation ratio
    K_t = P_(t+h) / (P_t (1+c_t)^years), the gains and c_eff, then summary statistics of each.
    `c` is a fixed annual benchmark rate; leave it out to use the article's rule, the trailing
    annualized log return with a floor. That rule takes the benchmark from the asset's own past
    return, which the article accepts only for assets with no close substitute. This is a reading
    in hindsight: each K_t uses a price that was not known at date t. Use prices that include
    reinvested distributions. Set `include_rows` to get every date, not only the summary.
    """
    r = core.price_history(prices, periods_per_year, horizon_periods, c, window_periods, floor)
    r["rows_computed"] = len(r["rows"])
    if not include_rows:
        del r["rows"]
    return _out(r)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
