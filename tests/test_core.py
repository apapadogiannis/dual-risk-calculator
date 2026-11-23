"""Checks of dualrisk.core against figures printed in the article and against its identities."""
import math, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from dualrisk import core as d


class Article(unittest.TestCase):
    def test_iso_gain_figure(self):
        # Section 6.1, text under Fig. 5: at c = 10% and five years, g = 0.2 gives K of about 1.12
        # and g = -0.2 gives K of about 0.88.
        self.assertEqual(round(d.ratio_from_gain(0.10, 0.2, 5), 2), 1.12)
        self.assertEqual(round(d.ratio_from_gain(0.10, -0.2, 5), 2), 0.88)

    def test_constant_bias_gives_K_independent_of_c(self):
        # Remark under eq. (12): a constant relative bias e gives K = 1/(1+e) at any c.
        b = [(t, 50 + 7 * t) for t in range(1, 9)]
        for c in (0.01, 0.08, 0.3):
            self.assertAlmostEqual(d.from_forecasts(c, b, [(t, 1.25 * x) for t, x in b])["K"], 1 / 1.25, places=12)

    def test_three_forms_of_the_identity(self):
        # Eqs. (27) to (29) for a single payoff, where the closed form is exact.
        r = d.from_forecasts(0.07, [(6, 1000)], [(6, 830)])
        self.assertAlmostEqual(r["v_own"] * r["K"], r["v_fair"], places=9)
        self.assertAlmostEqual(r["v_own"] * (1 + r["gain"] / 1.07 ** 6), r["v_fair"], places=9)
        self.assertAlmostEqual(830 / (1 + r["c_eff"]) ** 6, r["v_fair"], places=9)
        self.assertAlmostEqual(r["c_eff"], r["c_eff_stream"], places=10)

    def test_stream_rate_solves_the_definition(self):
        b, o = [(t, 100) for t in range(1, 6)], [(t, 90) for t in range(1, 6)]
        r = d.from_forecasts(0.08, b, o)
        self.assertAlmostEqual(d.present_value(o, r["c_eff_stream"]), r["v_fair"], places=8)

    def test_interpretation_signs(self):
        # Section 6.2: K > 1 gives c_eff < c, K < 1 gives c_eff > c, K = 1 gives c.
        self.assertLess(d.effective_rate(0.08, 1.2, 5), 0.08)
        self.assertGreater(d.effective_rate(0.08, 0.8, 5), 0.08)
        self.assertAlmostEqual(d.effective_rate(0.08, 1.0, 5), 0.08, places=14)

    def test_perpetuity(self):
        r = d.perpetuity(0.08, 0.02, 100, 90)
        self.assertAlmostEqual(90 / (r["c_eff"] - 0.02), r["v_fair"], places=9)      # eq. (34)

    def test_clearing_price(self):
        # Eq. (15), and the limit of large depth; mean(1/K) is not 1/mean(K).
        r = d.clearing_price(1.0, [0.9, 1.0, 1.1], supply=1, depth=5)
        self.assertAlmostEqual(r["price"], (1 / .9 + 1 + 1 / 1.1) / 3 - 0.2, places=12)
        self.assertGreater(r["mean_inverse_K"], 1 / r["mean_K"])

    def test_price_proxy_forms(self):
        # Eq. (38): the three forms of the realized gain agree.
        r = d.price_proxy(80, 131, 0.09, 3)
        self.assertAlmostEqual(r["gain"], 1.09 ** 3 * (r["K"] - 1), places=12)
        self.assertAlmostEqual(r["gain"], (131 - 80 * 1.09 ** 3) / 80, places=12)

    def test_history_matches_proxy(self):
        p = [100 * math.exp(0.003 * i + 0.05 * math.sin(i)) for i in range(300)]
        h = d.price_history(p, 52, c=0.06)
        row = h["rows"][17]
        self.assertAlmostEqual(row["K"], d.price_proxy(p[17], p[17 + 52], 0.06, 1)["K"], places=12)
        own = d.price_history(p, 52)
        self.assertEqual(own["rows"][0]["index"], 105)
        self.assertTrue(all(r["c"] >= 0.03 for r in own["rows"]))

    def test_bad_inputs_are_refused(self):
        for call in (lambda: d.perpetuity(0.02, 0.05, 1, 1), lambda: d.valuation_ratio(1, 0),
                     lambda: d.present_value([(0, 1)], 0.05), lambda: d.price_history([1, 2, 3])):
            self.assertRaises(d.InputError, call)


if __name__ == "__main__":
    unittest.main()
