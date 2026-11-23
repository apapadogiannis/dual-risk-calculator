"""The guide stored in api/ is the one the build writes, it names every tool the server offers, and
the page and the guide give the same article and licence."""
import pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from dualrisk import core
from dualrisk.server import NAME, REGISTRY

with tempfile.TemporaryDirectory() as tmp:
    out, api = pathlib.Path(tmp) / "site", pathlib.Path(tmp) / "api"
    build.build(out, api)
    for name in ("llms.txt", "example.json"):
        assert (ROOT / "api" / name).read_text() == (api / name).read_text(), f"api/{name} is not what the build writes; run build.py"
    guide, page = (api / "llms.txt").read_text(), (out / "index.html").read_text()
    assert not (out / "SKILL.md").exists() and not (ROOT / "api" / "SKILL.md").exists()
    assert "apapadogiannis/main/skill/SKILL.md" in guide and "apapadogiannis/blob/main/skill/SKILL.md" in page
import json
ex = json.loads((ROOT / "api" / "example.json").read_text())
again = core.from_forecasts(ex["inputs"]["c"], ex["inputs"]["benchmark"], ex["inputs"]["own"])
assert all(abs(ex["results"][k] - again[k]) < 1e-9 for k in ex["fields"]), "example.json does not follow from its inputs"
cfg = json.loads((ROOT / "mcp.json").read_text())["mcpServers"][NAME]
assert f"`{NAME}`" in guide and f"claude mcp add {NAME} " in (ROOT / "README.md").read_text(), "one server name everywhere"
assert " ".join([cfg["command"], *cfg["args"]]) == build.INSTALL and build.INSTALL in (ROOT / "README.md").read_text()
assert len(REGISTRY) == 6
for name, _ in REGISTRY:
    assert name in guide, name
doi = "10.1016/j.finr.2026.100096"
assert doi in core.CITATION and all(doi in t for t in (guide, page))
assert all("CC BY 4.0" in t for t in (guide, page)) and "MIT License" in guide and "MIT License" in page
src = (ROOT / "dualrisk" / "core.py").read_text()
for eq in ("eq. (11)", "eq. (21)", "eq. (26)", "eq. (25)"):
    assert eq in src
print("api/ is what the build writes; guide and page agree on tools, article and licence")
