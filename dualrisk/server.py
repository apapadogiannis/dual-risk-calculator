"""MCP server for the dual-risk DCF calculations.

Runs on the user's own machine over stdio. It computes from the numbers it is
given and nothing else: no network access, no stored data, no forecasts.

    python -m dualrisk.server
"""
from __future__ import annotations

import functools
from typing import Annotated, Any

from typing_extensions import TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from . import __version__, core

NAME = "dual-risk"        # the one name of this server: in mcp.json, the README, the guide and the skill

NOTE = ("Computed with the formulas of the cited article from the inputs given. "
        "It describes those inputs; it is not a forecast or a recommendation.")

mcp = MCPServer(
    NAME,
    version=__version__,
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
        except (ArithmeticError, IndexError, TypeError) as exc:
            raise ToolError("these inputs cannot be computed (" + type(exc).__name__ + "): check that rates "
                            "are decimals, that every benefit is a [time, amount] pair and that no number "
                            "is extreme") from exc
    REGISTRY.append((fn.__name__, fn.__doc__.strip().splitlines()[0]))
    return mcp.tool()(run)


class Result(TypedDict, total=False):
    """What every tool returns. Fields a tool does not compute are left out."""
    c: Annotated[float, Field(description="Benchmark rate used, a decimal per period")]
    horizon: Annotated[float, Field(description="Horizon h in periods: the last benefit date, or the one given")]
    v_fair: Annotated[float, Field(description="Present value of the benchmark forecast at c")]
    v_own: Annotated[float, Field(description="Present value of the examined forecast at c, or the price")]
    K: Annotated[float, Field(description="Valuation ratio v_fair / v_own. Above 1: below the benchmark fair value")]
    gain: Annotated[float, Field(description="Gain of capital g = (1+c)^h (K-1), over the whole horizon, not per period")]
    growth_factor_benchmark: Annotated[float, Field(description="(1+c)^h")]
    growth_factor_expected: Annotated[float, Field(description="(1+c)^h K")]
    expected_return_per_period: Annotated[float, Field(description="(1+c) K^(1/h) - 1, a decimal per period, from eq. (20). Exact for a single payoff at the horizon; for a stream it is not the internal rate of return")]
    c_eff: Annotated[float, Field(description="Effective rate, closed form (1+c) K^(-1/h) - 1, a decimal per period. Not an expected return")]
    c_eff_stream: Annotated[float | None, Field(description="Effective rate solved on the examined stream itself (eq. 25), a decimal per period. null when that stream has a negative amount, where the definition does not apply")]
    reading: Annotated[str, Field(description="K in words")]
    growth: Annotated[float, Field(description="Perpetuity growth rate, a decimal per period")]
    value_wedge: Annotated[float, Field(description="v_fair minus v_own")]
    mean_inverse_K: Annotated[float, Field(description="Weighted mean of 1/K across agents")]
    mean_K: Annotated[float, Field(description="Weighted mean of K across agents")]
    clearing_wedge: Annotated[float, Field(description="Q / lambda, the price concession that clears net supply")]
    price: Annotated[float, Field(description="Market-clearing price")]
    price_minus_fair: Annotated[float, Field(description="Clearing price minus v_fair")]
    price_is_non_negative: Annotated[bool, Field(description="False when the linear demand gives a negative price")]
    periods_per_year: Annotated[int, Field(description="Rows of the price series per year")]
    horizon_periods: Annotated[int, Field(description="Horizon in rows of the series")]
    horizon_years: Annotated[float, Field(description="Horizon in years")]
    c_rule: Annotated[str, Field(description="How c_t was set: fixed, or the trailing-return rule with its floor")]
    summary: Annotated[dict[str, Any], Field(description="For each of c, K, raw_gain, gain, c_eff: count, mean, std, min, q25, median, q75, max, skew")]
    rows: Annotated[list[dict[str, float]], Field(description="One record per date: index, c, K, raw_gain, gain, c_eff")]
    rows_computed: Annotated[int, Field(description="Number of dates the back-test covered")]
    warnings: Annotated[list[str], Field(description="Things to tell the user about the inputs, for example a rate that looks like a percentage. Empty when there is nothing to say")]
    source: Annotated[str, Field(description="The article the formulas come from; name it when reporting a result")]
    note: Annotated[str, Field(description="What the result is and is not")]


def _out(result: dict, **rates) -> Result:
    warnings = [w for w in (core.rate_warning(v, k) for k, v in rates.items()) if w]
    return {**result, "warnings": warnings, "source": core.CITATION, "note": NOTE}


Rate = Annotated[float, Field(description="Benchmark discount rate per period as a decimal: 0.08 for 8%. Above -1")]
Stream = Annotated[list[list[float]], Field(
    description="Expected benefits as [time, amount] pairs, time > 0 in periods from the valuation date, "
                "for example [[1, 100], [2, 104]]. Any number of periods")]


@tool
def compare_forecasts(c: Rate, benchmark: Stream, own: Stream) -> Result:
    """Split the gap between two forecasts of the same asset into c and K.

    `benchmark` is the reference (unbiased) forecast and `own` the forecast being examined, each a
    list of [time, expected benefit]. Both are discounted at the benchmark rate `c`. Returns the two
    present values, K, the gain of capital g = (1+c)^h (K-1), and the effective rate c_eff: the single
    rate that would make `own` worth the benchmark value. `c_eff` is the article's closed form;
    `c_eff_stream` solves the general definition and differs from it when benefits arrive over time.
    """
    return _out(core.from_forecasts(c, benchmark, own), c=c)


@tool
def compare_with_price(c: Rate, benchmark: Stream,
                       price: Annotated[float, Field(description="Observed price, positive, in the units of the benefits")]
                       ) -> Result:
    """Set a forecast against an observed price.

    The forecast, a list of [time, expected benefit], is discounted at `c` to give the fair value;
    the price stands in for the valuation. Returns K = fair value / price, the gain of capital, the
    expected return per period if the forecast is right, (1+c) K^(1/h) - 1, and c_eff.
    """
    return _out(core.against_price(c, benchmark, price), c=c)


@tool
def perpetuity(c: Rate,
               growth: Annotated[float, Field(description="Growth rate per period as a decimal, above -1 and below c")],
               benefit_fair: Annotated[float, Field(description="First-period benefit under the benchmark forecast, positive")],
               benefit_own: Annotated[float, Field(description="First-period benefit under the examined forecast, positive")]
               ) -> Result:
    """Constant-growth (Gordon) case: same growth under both beliefs, different first-period benefit.

    Returns both values, K, the value wedge and c_eff = (c - growth) / K + growth.
    """
    return _out(core.perpetuity(c, growth, benefit_fair, benefit_own), c=c, growth=growth)


@tool
def convert(c: Rate,
            horizon: Annotated[float, Field(description="Horizon h in periods, positive")],
            K: Annotated[float | None, Field(description="Valuation ratio, positive. Give this or gain")] = None,
            gain: Annotated[float | None, Field(description="Gain of capital over the whole horizon. Give this or K")] = None
            ) -> Result:
    """Convert between K and the gain of capital g at a given c and horizon, and give c_eff.

    Give exactly one of `K` or `gain`.
    """
    if (K is None) == (gain is None):
        raise ValueError("give exactly one of K or gain")
    if K is None:
        K = core.ratio_from_gain(c, gain, horizon)
    return _out({"c": c, "horizon": horizon, "K": K, "gain": core.gain_of_capital(c, K, horizon),
                 "c_eff": core.effective_rate(c, K, horizon)}, c=c)


@tool
def market_clearing_price(
        v_fair: Annotated[float, Field(description="Benchmark fair value, positive")],
        ratios: Annotated[list[float], Field(description="The K of each group of agents, all positive")],
        weights: Annotated[list[float] | None, Field(description="Share of agents at each K, same length as ratios; "
                                                                 "equal shares if left out")] = None,
        supply: Annotated[float, Field(description="Net supply Q, zero or more")] = 1.0,
        depth: Annotated[float, Field(description="Market depth lambda, positive")] = 1.0) -> Result:
    """Price that clears a market of agents who each value the asset at v_fair / K_i.

    Linear demand with depth `depth` (lambda) and net supply `supply` (Q):
    P = v_fair * mean(1/K) - Q / lambda. `weights` are the shares of agents at each K.
    """
    return _out(core.clearing_price(v_fair, ratios, weights, supply, depth))


@tool
def price_history(
        prices: Annotated[list[float], Field(description="Total-return prices, oldest first, all positive")],
        periods_per_year: Annotated[int, Field(description="Rows per year: 52 weekly, 12 monthly, 252 daily")] = 52,
        horizon_periods: Annotated[int | None, Field(description="Horizon in rows; one year if left out")] = None,
        c: Annotated[float | None, Field(description="Fixed annual benchmark rate as a decimal; leave out for the "
                                                     "article's trailing-return rule")] = None,
        window_periods: Annotated[int | None, Field(description="Trailing window in rows; two years if left out")] = None,
        floor: Annotated[float, Field(description="Lowest c_t the trailing rule may give, a decimal a year")] = 0.03,
        include_rows: Annotated[bool, Field(description="Return every date, not only the summary")] = False) -> Result:
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
    return _out(r, c=c, floor=floor)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
