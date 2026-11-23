# Reference results

Stored results of the replication package of the article,
https://github.com/apapadogiannis/dual-risk-dcf, copied on 23 November 2026.

| File | What it is |
|---|---|
| `weekly_prices.csv` | the weekly prices the package computes from its stored daily data |
| `weekly_series.csv` | the package's weekly c, K, raw gain and c_eff, by asset |
| `table4_K_stats.csv` | the package's statistics of K (Table 4 of the article) |

`tests/test_continuity.py` runs the calculator's price history on `weekly_prices.csv` and must
reproduce the other two files. The Bitcoin prices are from the Coin Metrics community data
(CC BY-NC 4.0), the equity series from the Kenneth R. French data library, and the gold series is
the close of SPDR Gold Shares; see the package for the terms of each.
