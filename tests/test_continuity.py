"""The calculator's price history, run on the weekly prices of the article's replication package,
must reproduce that package's stored weekly series and its statistics of K (Table 4)."""
import csv, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dualrisk import core

def rows(name):
    with open(ROOT / "reference" / name, newline="") as f:
        return list(csv.DictReader(f))

prices, series, stats = rows("weekly_prices.csv"), rows("weekly_series.csv"), {r["asset"]: r for r in rows("table4_K_stats.csv")}
n, worst = 0, 0.0
def close(a, b):
    global n, worst
    e = abs(a - b) / max(1e-12, abs(b)); n += 1
    if abs(a - b) < 1e-10:        # the reference files carry twelve significant digits
        return
    worst = max(worst, e)
    assert e < 1e-9, (a, b)

for asset in ("BTC", "US_MARKET", "GLD"):
    h = core.price_history([float(r[asset]) for r in prices], 52)       # the article's rule: two-year window, 3% floor
    ref = [r for r in series if r["asset"] == asset and r["K"] != ""]
    assert len(h["rows"]) == len(ref) == 367
    for got, want in zip(h["rows"], ref):
        assert prices[got["index"]]["week_ending"] == want["week_ending"]
        for k in ("c", "K", "c_eff"):
            close(got[k], float(want[k]))
        close(got["raw_gain"], float(want["g_raw"]))
    s = h["summary"]["K"]
    for k in ("mean", "std", "min", "q25", "median", "q75", "max", "skew"):
        close(s[k], float(stats[asset][k]))
print(f"calculator reproduces the replication package: {n} numbers, largest relative difference {worst:.1e}")
