"""Start the server over stdio as an MCP client would, list its tools, call each once and
compare the answers with dualrisk.core. A refused input must come back in words."""
import asyncio, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dualrisk import core
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "dualrisk.server"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            print("tools:", [t.name for t in tools])
            results = {}
            calls = {
              "compare_forecasts": {"c": .08, "benchmark": [[t, 100] for t in range(1, 6)], "own": [[t, 90] for t in range(1, 6)]},
              "compare_with_price": {"c": .08, "benchmark": [[5, 1000]], "price": 600},
              "perpetuity": {"c": .08, "growth": .02, "benefit_fair": 100, "benefit_own": 90},
              "convert": {"c": .10, "horizon": 5, "gain": .2},
              "market_clearing_price": {"v_fair": 1, "ratios": [.9, 1, 1.1], "depth": 5},
              "price_history": {"prices": [100 * 1.002 ** i for i in range(200)], "c": .05},
            }
            assert set(calls) == {t.name for t in tools}
            for name, args in calls.items():
                res = await s.call_tool(name, args)
                assert not res.is_error, res.content
                d = json.loads(res.content[0].text)
                assert d["source"] == core.CITATION, name
                results[name] = d
            a = calls["compare_forecasts"]; assert results["compare_forecasts"]["K"] == core.from_forecasts(a["c"], a["benchmark"], a["own"])["K"]
            a = calls["compare_with_price"]; assert results["compare_with_price"]["c_eff"] == core.against_price(a["c"], a["benchmark"], a["price"])["c_eff"]
            assert results["convert"]["K"] == core.ratio_from_gain(.10, .2, 5)
            assert results["price_history"]["rows_computed"] == 148 and "rows" not in results["price_history"]
            bad = await s.call_tool("perpetuity", {"c": .02, "growth": .05, "benefit_fair": 1, "benefit_own": 1})
            assert bad.is_error and "growth rate must be below c" in bad.content[0].text
            print(f"server answers on {len(tools)} tools and agrees with dualrisk.core; a refused input is explained in words")
asyncio.run(main())
