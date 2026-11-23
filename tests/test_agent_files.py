"""The guide and the skill stored in api/ are the ones the build writes, they name every tool
the server offers, and the page, the guide and the skill give the same article and licence."""
import pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from dualrisk import core
from dualrisk.server import REGISTRY

with tempfile.TemporaryDirectory() as tmp:
    out, api = pathlib.Path(tmp) / "site", pathlib.Path(tmp) / "api"
    build.build(out, api)
    for name in ("llms.txt", "SKILL.md", "example.json"):
        assert (ROOT / "api" / name).read_text() == (api / name).read_text(), f"api/{name} is not what the build writes; run build.py"
    guide, skill, page = (api / "llms.txt").read_text(), (api / "SKILL.md").read_text(), (out / "index.html").read_text()
import json
ex = json.loads((ROOT / "api" / "example.json").read_text())
again = core.from_forecasts(ex["inputs"]["c"], ex["inputs"]["benchmark"], ex["inputs"]["examined"])
assert all(abs(ex["results"][k] - again[k]) < 1e-9 for k in ex["fields"]), "example.json does not follow from its inputs"
assert len(REGISTRY) == 6
for name, _ in REGISTRY:
    assert name in guide and name in skill, name
doi = "10.1016/j.finr.2026.100096"
assert doi in core.CITATION and all(doi in t for t in (guide, skill, page))
assert all("CC BY 4.0" in t for t in (guide, skill, page)) and "MIT License" in guide and "MIT License" in page
src = (ROOT / "dualrisk" / "core.py").read_text()
for eq in ("eq. (11)", "eq. (21)", "eq. (26)", "eq. (25)"):
    assert eq in src
print("api/ is what the build writes; guide, skill and page agree on tools, article and licence")
