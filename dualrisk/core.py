"""Dual-risk DCF: the calculations of

    A. Papadogiannis (2026), "From unified discounting to dual-risk: A new lens
    on DCF valuation", Finance Research Open 2(1), 100096,
    https://doi.org/10.1016/j.finr.2026.100096

Standard library only. Every function names the equation of the article it
implements. Rates are per period (a year unless the caller says otherwise) and
times are counted in periods from the valuation date.

A benefit stream is a list of (time, amount) pairs with time > 0.
"""
from __future__ import annotations

import math

CITATION = ('A. Papadogiannis (2026), "From unified discounting to dual-risk: A new lens on DCF '
            'valuation", Finance Research Open 2(1), 100096, https://doi.org/10.1016/j.finr.2026.100096')


class InputError(ValueError):
    """An input the article's formulas are not defined for."""


def _stream(benefits):
    out = []
    for item in benefits:
        try:
            pair = tuple(item)
        except TypeError:
            pair = ()
        if len(pair) != 2:
            raise InputError("each benefit must be a [time, amount] pair")
        try:
            t, x = float(pair[0]), float(pair[1])
        except (TypeError, ValueError):
            raise InputError("times and amounts must be finite numbers") from None
        if not (math.isfinite(t) and math.isfinite(x)):
            raise InputError("times and amounts must be finite numbers")
        if t <= 0:
            raise InputError("benefit times must be after the valuation date (time > 0)")
        out.append((t, x))
    if not out:
        raise InputError("the benefit stream is empty")
    return out


def _rate(c, name="c"):
    c = float(c)
    if not math.isfinite(c) or c <= -1:
        raise InputError(f"{name} must be a rate above -100%")
    return c


def _positive(x, what):
    """A finite number above zero, or an InputError that names it."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        raise InputError(f"{what} must be a positive number") from None
    if not math.isfinite(x) or x <= 0:
        raise InputError(f"{what} must be a positive number")
    return x


def _finite(x, what):
    try:
        x = float(x)
    except (TypeError, ValueError):
        raise InputError(f"{what} must be a finite number") from None
    if not math.isfinite(x):
        raise InputError(f"{what} must be a finite number")
    return x


def rate_warning(c, name="c"):
    """Rates are decimals. A rate above 1 (100% per period) is almost always a
    percentage typed as a whole number; this returns a sentence saying so, or None."""
    try:
        c = float(c)
    except (TypeError, ValueError):
        return None
    if math.isfinite(c) and c > 1:
        return (f"{name} = {c:g} was read as {c:.0%} per period. Rates are decimals: "
                f"enter {c / 100:g} for {c:g}%.")
    return None


def present_value(benefits, c):
    """Present value of a stream at rate c. Article eqs. (1) and (2)."""
    c = _rate(c)
    return math.fsum(x / (1 + c) ** t for t, x in _stream(benefits))


def terminal_equivalent(benefits, c, horizon=None):
    """The stream compounded at c to the horizon (default: its last date).
    Article, Section 6.2, "terminal-equivalent normalization"."""
    c = _rate(c)
    s = _stream(benefits)
    T = max(t for t, _ in s) if horizon is None else float(horizon)
    return math.fsum(x * (1 + c) ** (T - t) for t, x in s)


def valuation_ratio(v_fair, v_own):
    """K = V_fair / V_own. Article eq. (11). K > 1: the valuation is below the
    benchmark (pessimism, undervaluation). K < 1: above it (optimism)."""
    try:
        v_fair, v_own = float(v_fair), float(v_own)
    except (TypeError, ValueError):
        raise InputError("both values must be positive for K to be defined") from None
    if not (math.isfinite(v_fair) and math.isfinite(v_own)) or v_fair <= 0 or v_own <= 0:
        raise InputError("both values must be positive for K to be defined")
    return v_fair / v_own


def gain_of_capital(c, K, horizon):
    """g = (1+c)^h (K - 1). Article eq. (21): the wedge between the expected
    growth factor (1+c)^h K, eq. (20), and the benchmark growth factor."""
    return (1 + _rate(c)) ** _positive(horizon, "the horizon") * (_finite(K, "K") - 1)


def ratio_from_gain(c, g, horizon):
    """K = 1 + g / (1+c)^h. Article eq. (24)."""
    return 1 + _finite(g, "the gain") / (1 + _rate(c)) ** _positive(horizon, "the horizon")


def effective_rate(c, K, horizon):
    """c_eff = (1+c) K^(-1/h) - 1. Article eq. (26), closed form under the
    terminal-equivalent normalization."""
    K, h = _positive(K, "K"), _positive(horizon, "the horizon")
    return (1 + _rate(c)) * K ** (-1 / h) - 1


def _pv_at(s, r):
    """Present value of a non-negative stream at rate r, for the solver. A
    discount factor too large for a float makes its term zero, and one too
    small makes the value infinite, so far dates do not stop the search."""
    terms = []
    for t, x in s:
        try:
            d = (1 + r) ** t
        except OverflowError:
            continue
        if d == 0.0:
            if x > 0:
                return math.inf
            continue
        terms.append(x / d)
    return math.fsum(terms)


def effective_rate_stream(own_benefits, v_fair, lo=-0.99, hi=1e6):
    """The rate r that makes the present value of the agent's own stream equal
    v_fair. Article eq. (25), the general definition. Found by bisection; needs
    non-negative benefits that are not all zero, as the article requires. Works
    for any number of periods (a monthly stream of many years included)."""
    s = _stream(own_benefits)
    if any(x < 0 for _, x in s) or not any(x > 0 for _, x in s):
        raise InputError("eq. (25) needs non-negative benefits that are not all zero")
    v_fair = _positive(v_fair, "the fair value")
    f = lambda r: _pv_at(s, r) - v_fair
    if f(lo) < 0 or f(hi) > 0:
        raise InputError("no rate between -99% and 1e6 equates the two values")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _reading(K):
    if abs(K - 1) < 1e-12:
        return "K = 1: the valuation equals the benchmark fair value"
    if K > 1:
        return "K > 1: the valuation is below the benchmark fair value (pessimistic forecast, or a price below fair value)"
    return "K < 1: the valuation is above the benchmark fair value (optimistic forecast, or a price above fair value)"


def _bundle(c, v_fair, v_own, h):
    try:
        return _bundle_unchecked(c, v_fair, v_own, h)
    except (OverflowError, ZeroDivisionError):
        raise InputError("the result is too large for these inputs: check the horizon, "
                         "the rate and the two values") from None


def _bundle_unchecked(c, v_fair, v_own, h):
    K = valuation_ratio(v_fair, v_own)
    return {
        "c": c, "horizon": h, "v_fair": v_fair, "v_own": v_own, "K": K,
        "gain": gain_of_capital(c, K, h),
        "growth_factor_benchmark": (1 + c) ** h,
        "growth_factor_expected": (1 + c) ** h * K,
        "expected_return_per_period": (1 + c) * K ** (1 / h) - 1,
        "c_eff": effective_rate(c, K, h),
        "reading": _reading(K),
    }


def from_forecasts(c, benchmark, own):
    """Two forecasts of the same asset, both discounted at the benchmark rate c.
    Returns V_fair (eq. 7), V_own (eq. 10), K (eq. 11), g (eq. 21), c_eff in
    closed form (eq. 26) and from the general definition (eq. 25). The two
    c_eff agree for a single payoff and differ a little for a stream."""
    c = _rate(c)
    b, o = _stream(benchmark), _stream(own)
    h = max(t for t, _ in b + o)
    out = _bundle(c, present_value(b, c), present_value(o, c), h)
    try:
        out["c_eff_stream"] = effective_rate_stream(o, out["v_fair"])
    except InputError:
        out["c_eff_stream"] = None
    return out


def against_price(c, benchmark, price):
    """A benchmark forecast set against an observed price, which stands in for
    the valuation V (article, footnote 2 and eq. 35). c_eff is the closed form;
    expected_return_per_period is the rate implied by eq. (20)."""
    c = _rate(c)
    b = _stream(benchmark)
    return _bundle(c, present_value(b, c), _positive(price, "the price"), max(t for t, _ in b))


def perpetuity(c, growth, benefit_fair, benefit_own):
    """Constant-growth perpetuity with the same growth under both beliefs.
    Article eqs. (30) to (34)."""
    c, gf = _rate(c), _finite(growth, "the growth rate")
    if gf <= -1:
        raise InputError("the growth rate must be above -100%")
    if not gf < c:
        raise InputError("the growth rate must be below c for the value to converge")
    bf = _positive(benefit_fair, "first-period benefits")
    bo = _positive(benefit_own, "first-period benefits")
    K = bf / bo
    return {"c": c, "growth": gf, "v_fair": bf / (c - gf), "v_own": bo / (c - gf), "K": K,
            "value_wedge": bf / (c - gf) - bo / (c - gf),
            "c_eff": (c - gf) / K + gf, "reading": _reading(K)}


def clearing_price(v_fair, ratios, weights=None, supply=1.0, depth=1.0):
    """Market-clearing price with linear demand. Article eqs. (13) to (15):
    P = V_fair * mean(1/K) - Q/lambda. `weights` are the shares of agents
    holding each K (equal if omitted)."""
    ks = [float(k) for k in ratios]
    if not ks or any(k <= 0 for k in ks):
        raise InputError("give at least one K, all positive")
    w = [1.0] * len(ks) if weights is None else [float(x) for x in weights]
    if len(w) != len(ks) or any(x < 0 for x in w) or sum(w) <= 0:
        raise InputError("weights must match the K values and be non-negative")
    if any(not math.isfinite(k) for k in ks) or any(not math.isfinite(x) for x in w):
        raise InputError("K values and weights must be finite numbers")
    v_fair = _positive(v_fair, "the fair value")
    depth = _positive(depth, "market depth (lambda)")
    supply = _finite(supply, "net supply")
    if supply < 0:
        raise InputError("net supply must not be negative")
    mean_inv = math.fsum(x / k for x, k in zip(w, ks)) / math.fsum(w)
    price = v_fair * mean_inv - supply / depth
    return {"mean_inverse_K": mean_inv, "mean_K": math.fsum(x * k for x, k in zip(w, ks)) / math.fsum(w),
            "clearing_wedge": supply / depth, "price": price, "price_minus_fair": price - v_fair,
            "price_is_non_negative": price >= 0}


def price_proxy(p_start, p_end, c, years=1.0):
    """The article's ex post proxy from two total-return prices. Eqs. (35) to
    (38): K = P_T / (P_t (1+c)^h), g = P_T/P_t - (1+c)^h. `c` is per year and
    `years` is the horizon. raw_gain = K - 1 is the "raw gain" the article's back-test
    reports, eq. (44)."""
    p0, p1 = _positive(p_start, "prices"), _positive(p_end, "prices")
    c, h = _rate(c), _positive(years, "the horizon")
    K = p1 / (p0 * (1 + c) ** h)
    return {"K": K, "gain": p1 / p0 - (1 + c) ** h, "raw_gain": K - 1,
            "c_eff": effective_rate(c, K, h), "realized_return_per_year": (p1 / p0) ** (1 / h) - 1}


def describe(values):
    """count, mean, std, min, quartiles, max and skewness, computed as the
    article's tables are: sample standard deviation (n - 1), quartiles by
    linear interpolation, and skewness m3 / m2^1.5 with no bias adjustment."""
    v = sorted(float(x) for x in values)
    n = len(v)
    if n == 0:
        return {"count": 0}
    mean = math.fsum(v) / n

    def q(p):
        pos = (n - 1) * p
        lo = math.floor(pos)
        hi = min(lo + 1, n - 1)
        return v[lo] + (v[hi] - v[lo]) * (pos - lo)

    out = {"count": n, "mean": mean, "std": None, "min": v[0], "q25": q(.25), "median": q(.5),
           "q75": q(.75), "max": v[-1], "skew": None}
    if n > 1:
        m2 = math.fsum((x - mean) ** 2 for x in v)
        out["std"] = math.sqrt(m2 / (n - 1))
        if n > 2 and m2 > 0:
            m3 = math.fsum((x - mean) ** 3 for x in v)
            out["skew"] = math.sqrt(n) * m3 / m2 ** 1.5
    return out


def price_history(prices, periods_per_year=52, horizon_periods=None, c=None,
                  window_periods=None, floor=0.03):
    """The article's back-test (Section 7.2) on any series of total-return prices.

    For each date t with a price `horizon_periods` later:
      c_t   = `c` if a fixed annual rate is given; otherwise the article's
              self-referential proxy max(floor, (P_t / P_{t-w})^(ppy/w) - 1):
              the annualized return over the trailing window of w periods
              ending at t. This is the rule of the article's back-test, the
              form under eq. (42) taken over the w returns ending at t;
      K_t   = P_{t+h} / (P_t (1+c_t)^years), eq. (43) for one year;
      raw_gain = K_t - 1, eq. (44); gain = (1+c_t)^years (K_t - 1), eq. (37);
      c_eff = (1+c_t) K_t^(-1/years) - 1, per year, eq. (26). For one year
              this is (1+c_t)/K_t - 1, the yearly rate shown in the article's
              Fig. 6 and Table 5.
    Defaults follow the article: horizon one year, window two years, floor 3%.
    Rows without a full window or without a later price are left out.
    """
    try:
        p = [float(x) for x in prices]
    except (TypeError, ValueError):
        raise InputError("prices must be positive numbers") from None
    if any(not math.isfinite(x) or x <= 0 for x in p):
        raise InputError("prices must be positive numbers")
    def whole(x, what):
        x = _positive(x, what)
        if x != int(x):
            raise InputError(f"{what} must be a whole number")
        return int(x)

    ppy = whole(periods_per_year, "periods_per_year")
    h = ppy if horizon_periods is None else whole(horizon_periods, "the horizon")
    w = 2 * ppy if window_periods is None else whole(window_periods, "the window")
    floor = _finite(floor, "the floor")
    if floor <= -1:
        raise InputError("the floor must be a rate above -100%")
    years = h / ppy
    fixed = None if c is None else _rate(c)
    first = 0 if fixed is not None else w
    if len(p) <= first + h:
        raise InputError(f"the series is too short: {len(p)} prices, at least {first + h + 1} needed")
    rows = []
    for t in range(first, len(p) - h):
        if fixed is not None:
            ct = fixed
        else:
            ct = max(float(floor), (p[t] / p[t - w]) ** (ppy / w) - 1)
        K = p[t + h] / (p[t] * (1 + ct) ** years)
        rows.append({"index": t, "c": ct, "K": K, "raw_gain": K - 1,
                     "gain": (1 + ct) ** years * (K - 1),
                     "c_eff": (1 + ct) * K ** (-1 / years) - 1})
    return {"periods_per_year": ppy, "horizon_periods": h, "horizon_years": years,
            "c_rule": "fixed" if fixed is not None else f"trailing {w} periods, floor {float(floor)}",
            "rows": rows,
            "summary": {k: describe(r[k] for r in rows) for k in ("c", "K", "raw_gain", "gain", "c_eff")}}
