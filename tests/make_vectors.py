"""Write tests/vectors.json: cases and the results of dualrisk.core on them.
The page's calculations are checked against this file by tests/check_page.mjs."""
import json, math, pathlib, random, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from dualrisk import core as d

rnd = random.Random(20260211)
cases = []
def add(fn, args, result): cases.append({"fn": fn, "args": args, "result": result})

for _ in range(40):
    c = rnd.uniform(-0.02, 0.25); n = rnd.randint(1, 12)
    bench = [[t, rnd.uniform(0, 200)] for t in range(1, n + 1)]; bench[-1][1] += 500
    own = [[t, x * rnd.uniform(0.5, 1.6)] for t, x in bench]
    add("fromForecasts", [c, bench, own], d.from_forecasts(c, bench, own))
    price = rnd.uniform(200, 2000)
    add("againstPrice", [c, bench, price], d.against_price(c, bench, price))
for n in (52, 60, 120, 162, 240, 600):      # long streams: monthly forecasts over many years
    c = rnd.uniform(0.001, 0.02)
    bench = [[t, rnd.uniform(50, 200)] for t in range(1, n + 1)]
    own = [[t, x * rnd.uniform(0.5, 1.6)] for t, x in bench]
    add("fromForecasts", [c, bench, own], d.from_forecasts(c, bench, own))
for _ in range(12):
    n = rnd.randint(140, 400); ppy = rnd.choice([12, 52]); p = [100.0]
    for _ in range(n): p.append(p[-1] * math.exp(rnd.gauss(0.002, 0.03)))
    add("priceHistory", [p, ppy, None, None, None, 0.03], d.price_history(p, ppy))
    add("priceHistory", [p, ppy, ppy // 2, 0.07, None, 0.03], d.price_history(p, ppy, ppy // 2, 0.07))
for r in cases:
    r["result"].pop("reading", None); r["result"].pop("c_rule", None)
pathlib.Path(__file__).with_name("vectors.json").write_text(json.dumps(cases))
print(len(cases), "cases")
