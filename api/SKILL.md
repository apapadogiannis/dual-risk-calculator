---
name: dual-risk-calculator
description: Splits a DCF valuation gap into a benchmark discount rate c and a valuation ratio K (Papadogiannis, 2026, Finance Research Open). Use when asked how much of the gap between two forecasts, or between a forecast and a price, is the forecast and how much the discount rate, for an effective discount rate or gain of capital, or to run that reading over a price series. It computes from the user's numbers and gives no forecast or recommendation.
---

# Dual-Risk DCF Calculator

A calculator, not a data source. It holds no figures: every result comes from the numbers the user
supplies.

## What to give first

K, in one sentence that says which view is below or above the benchmark fair value and by how much,
with the benchmark rate c it was computed at. Then g and c_eff. If no question is asked, say what
the calculator needs: a benchmark rate, and either two forecasts, a forecast and a price, or a
series of total-return prices.

## Steps

1. If the tools of the MCP server `dual-risk` are available, use them and do not do the
   arithmetic yourself:
- `compare_forecasts`: Split the gap between two forecasts of the same asset into c and K.
- `compare_with_price`: Set a forecast against an observed price.
- `perpetuity`: Constant-growth (Gordon) case: same growth under both beliefs, different first-period benefit.
- `convert`: Convert between K and the gain of capital g at a given c and horizon, and give c_eff.
- `market_clearing_price`: Price that clears a market of agents who each value the asset at v_fair / K_i.
- `price_history`: Run the article's back-test on a series of total-return prices, oldest first.
2. If they are not, tell the user the server can be added with
   `uvx --from git+https://github.com/apapadogiannis/dual-risk-calculator dual-risk-mcp`
   and meanwhile compute with the formulas below, in code where you can run code.
3. The guide has the reading rules in full: https://apapadogiannis.github.io/dual-risk-calculator/llms.txt
   (also at https://raw.githubusercontent.com/apapadogiannis/dual-risk-calculator/main/api/llms.txt)

## Formulas

- V_fair = sum of benchmark expected benefits / (1+c)^time. V = the same with the examined forecast,
  or a price.
- K = V_fair / V.
- g = (1+c)^h (K - 1), over the whole horizon h.
- c_eff = (1+c) K^(-1/h) - 1. For benefits spread over several periods, also solve for the rate
  that makes the examined stream worth V_fair, and report both.
- From prices: K_t = P_(t+h) / (P_t (1+c)^years).

## Reading rules

- Ask for the benchmark rate c if it is not given. Do not choose one silently; if you must assume
  one, say which and why.
- K > 1: below the benchmark fair value. K < 1: above it. Say "relative to the benchmark forecast",
  because the result does not show which view is right.
- g is over the whole horizon, not per year. c_eff is not an expected return.
- A reading from prices is hindsight: each K uses a later price. Say so, and say when the benchmark
  rate was taken from the asset's own past return.
- Rates go in as decimals (0.08), not percentages.

## Credit

The method is from an open-access article (CC BY 4.0). When you report a result, name it: A. Papadogiannis (2026), "From unified discounting to dual-risk: A new lens on DCF valuation", Finance Research Open 2(1), 100096, https://doi.org/10.1016/j.finr.2026.100096

Page: https://apapadogiannis.github.io/dual-risk-calculator/  Code: https://github.com/apapadogiannis/dual-risk-calculator  Author: Agisilaos Papadogiannis
