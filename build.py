"""Build the site into _site/ and write the files for programs and AI agents into api/.

    python3 -I build.py            writes _site/ and api/
    python3 -I build.py OUT API    writes elsewhere (used by tests/test_agent_files.py)

The guide (llms.txt) is written here and never by hand. The list of
tools in them is read from the server itself.
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from dualrisk import __version__, core          # noqa: E402
from dualrisk.server import NAME, REGISTRY      # noqa: E402

PAGE = "https://apapadogiannis.github.io/dual-risk-calculator/"
REPO = "https://github.com/apapadogiannis/dual-risk-calculator"
RAW = "https://raw.githubusercontent.com/apapadogiannis/dual-risk-calculator/main/"
INSTALL = f"uvx --from git+{REPO} dual-risk-mcp"
ARCHIVE = "https://doi.org/10.5281/zenodo.24465124"
CITE = (f'A. Papadogiannis (2026), "Dual-Risk DCF Calculator", version {__version__}, Zenodo, {ARCHIVE}, '
        f"together with the article: {core.CITATION}")


def guide() -> str:
    tools = "\n".join(f"- {name}: {what}" for name, what in REGISTRY)
    ex = core.from_forecasts(0.08, [(t, 100) for t in range(1, 6)], [(t, 90) for t in range(1, 6)])
    return f"""# Dual-Risk DCF Calculator

A calculator for the dual-risk reading of a discounted cash flow value: it keeps the benchmark
discount rate c fixed and puts the gap between two views of an asset into one number, the valuation
ratio K = V_fair / V. It computes from the numbers the user gives. It holds no market data.

Maintained by Agisilaos Papadogiannis. Version {__version__}. It changes only when the code changes;
there is no data feed.

## What it computes

- Two forecasts of the same asset, or a forecast and a price: both present values at c, K, the gain
  of capital g = (1+c)^h (K-1), and the effective rate c_eff = (1+c) K^(-1/h) - 1.
- The constant-growth perpetuity case, and conversion between K and g.
- The price that clears a market of agents with different K (linear demand).
- The article's back-test on any series of total-return prices: for each date, the realized
  K_t = P_(t+h) / (P_t (1+c_t)^years), the gains, c_eff, and summary statistics.

## What this adds

- The formulas are implemented once, each tied to the equation of the published article it comes
  from, and tested against figures printed in that article and against its identities.
- The page and the server run two implementations (JavaScript and Python). A test runs both on the
  same cases and fails if any number differs beyond a relative 1e-9.
- c_eff is given two ways where they differ. The article's closed form is exact for a single payoff
  at the horizon. For benefits that arrive over several periods, solving the definition on the
  stream gives a different rate (`c_eff_stream`). For a level five-period stream forecast 10% low
  at c = 8%, the closed form gives {ex['c_eff']:.1%} and the definition {ex['c_eff_stream']:.1%}.
- `c_eff_stream` is null when the examined stream has a negative amount: the definition needs
  non-negative benefits. Streams of any length are solved, monthly ones over many years included.
- `expected_return_per_period` is (1+c) K^(1/h) - 1. It is exact for a single payoff at the horizon;
  for a stream bought at a price it is not the internal rate of return.
- Inputs the formulas are not defined for (a growth rate at or above c or at or below -100%, a value
  that is not a positive number, a series too short) are refused with a sentence that says why, not
  answered with a number.
- A rate above 1 is computed as given and flagged in `warnings`, since it is usually a percentage
  typed as a whole number (8 for 0.08). Report the warning to the user.

## How to use it

1. As an MCP server on the user's own machine (stdio, no network access), named `{NAME}`:
   `{INSTALL}`
   Every tool describes its parameters and returns one record with described fields (the output
   schema), plus `warnings`, `source` and `note`.
   Tools:
{tools}
   If these tools are available to you, use them and do not do the arithmetic yourself. If they are
   not, tell the user the server can be added with the line above, and meanwhile compute with the
   formulas of this guide, in code where you can run code. Ask for the benchmark rate c if it is not
   given: do not choose one silently.
2. As a page for a person: {PAGE}
3. As a Python module with no dependencies: {RAW}dualrisk/core.py
   (the same file in the repository: {REPO}/blob/main/dualrisk/core.py)

## How to read the figures

- Rates are decimals per period (0.08 is 8%), a year unless the caller says otherwise. Times are
  counted in periods from the valuation date; a benefit stream is a list of [time, amount] with
  time > 0.
- K > 1: the valuation or price is below the benchmark fair value (the article calls this pessimism
  or undervaluation). K < 1: above it. K = 1: no gap.
- "Fair value" means the benchmark forecast discounted at c. It is fair relative to that forecast
  and that rate, both supplied by the user.
- `gain` is a difference of growth factors over the whole horizon, not a rate per period.
  `expected_return_per_period` = (1+c) K^(1/h) - 1 is the per-period rate with the same content; it
  assumes interim benefits are reinvested at c.
- K > 1 gives c_eff below c, and K < 1 gives c_eff above c. c_eff is the rate a one-rate DCF would
  need in order to turn the examined forecast into the fair value. It is not an expected return.
- In the price history, `raw_gain` is K - 1, the quantity the article's tables call the raw gain;
  `gain` is (1+c)^years (K - 1). `c` and `c_eff` are per year. Statistics are computed as in the
  article's tables: sample standard deviation, linearly interpolated quartiles, and skewness
  without bias adjustment.
- With no fixed c, the price history uses the rule of the article's back-test: the annualized
  return over the trailing window ending at the date, with a floor. That benchmark comes from the asset's own
  past return, which the article accepts only for assets with no close substitute.

## Do not use this for

- A forecast or a recommendation. K measures the distance between two views at a given c. It does
  not say which view is right.
- Today's K from prices. The price-history reading needs the price one horizon later, so its last
  result is always one horizon old.
- Choosing c. The benchmark rate is an input, and every result depends on it.
- The figures of the article itself (its tables for VTI, GLD and BTC-USD). Those belong to the
  article and its replication package.

## Source, licence and credit

Method: {core.CITATION} (open access, CC BY 4.0).
Code: MIT License. Text and figures of the page: CC BY 4.0, whose one condition is credit.
Cite as: {CITE}
Description: an open-source calculator by the author of the article, implementing its formulas.

A skill for an AI assistant: one skill covers this calculator and the rest of the author's work, and
sends the assistant to this guide. https://raw.githubusercontent.com/apapadogiannis/apapadogiannis/main/skill/SKILL.md
"""


def example() -> str:
    """api/example.json: one worked case, computed here, for pages that describe the calculator."""
    c, bench = 0.08, [[t, 100.0] for t in range(1, 6)]
    own = [[t, 90.0] for t in range(1, 6)]
    r = core.from_forecasts(c, bench, own)
    r.pop("reading")
    r = {k: round(v, 10) for k, v in r.items()}     # ten decimals: the same file on every machine
    return json.dumps({
        "what": "A worked example of the Dual-Risk DCF Calculator: two forecasts of the same asset, the examined "
                "one 10% below the benchmark in every year, both discounted at the benchmark rate.",
        "inputs": {"c": c, "benchmark": bench, "own": own, "periods": "years"},
        "results": r,
        "fields": {"v_fair": "present value of the benchmark forecast at c",
                   "v_own": "present value of the examined forecast at c",
                   "K": "valuation ratio, v_fair / v_own",
                   "gain": "gain of capital over the whole horizon, (1+c)^h (K-1)",
                   "c_eff": "effective rate, closed form (1+c) K^(-1/h) - 1, a fraction a year",
                   "c_eff_stream": "effective rate solved on the yearly amounts, a fraction a year",
                   "expected_return_per_period": "(1+c) K^(1/h) - 1, a fraction a year"},
        "page": PAGE, "licence": "CC BY 4.0", "cite_as": CITE}, indent=1) + "\n"


def build(out: pathlib.Path, api: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    api.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "site" / "index.html", out / "index.html")
    (out / ".nojekyll").write_text("")
    for name, text in (("llms.txt", guide()), ("example.json", example())):
        (api / name).write_text(text)
        (out / name).write_text(text)


if __name__ == "__main__":
    a = sys.argv[1:]
    build(pathlib.Path(a[0]) if a else ROOT / "_site", pathlib.Path(a[1]) if len(a) > 1 else ROOT / "api")
    print("built")
