"""Review UI smoke test. Run from repo root: .venv\\Scripts\\python -m tests.test_app"""
import json
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from dejavu.engine import scan
from dejavu.explain import verbatim
from dejavu.report import payload, render

# verbatim: rare identical lines count, boilerplate shared by 3+ files does not
a = "x = 1\n    long long weird_total = 0; // tally\n    int helper_value = 42;\n"
b = "y = 2\n    int helper_value = 42;\n    long long weird_total = 0; // tally\n"
assert verbatim(a, b) == [(2, 3, "long long weird_total = 0; // tally"), (3, 2, "int helper_value = 42;")]
assert verbatim(a, b, {"int helper_value = 42;"}) == [(2, 3, "long long weird_total = 0; // tally")]

# payload: demo ranks the 6 true copies first, with name roles as evidence
data = payload(scan(Path(__file__).parent / "problems"))
kind = lambda i: data["files"][i]["name"].split("/")[1].split(".")[0]
assert all({kind(p["a"]), kind(p["b"])} == {"orig", "ai_rewrite"} for p in data["pairs"][:6])
assert ("distance", "dist", 7) in data["pairs"][0]["ren"], data["pairs"][0]["ren"]

# render: submission text can't close the data <script> block
evil = {"id": "x", "files": [{"name": "a.py", "lang": "python", "src": "</script><script>alert(1)</script>",
                              "flags": []}], "pairs": [], "totalPairs": 0, "totalFiles": 1, "seconds": 0}
page = render(evil)
assert "alert(1)</script>" not in page and "\\u003c/script>" in page
blob = re.search(r"const DATA = (.*?);\n", page).group(1)
assert json.loads(blob)["files"][0]["src"].startswith("</script>")
# host theme: only "light"/"dark" pass through; anything else falls back to the reviewer's OS setting
assert "const HOST_THEME = null;" in page
assert 'const HOST_THEME = "dark";' in render(evil, "dark")
assert "const HOST_THEME = null;" in render(evil, '"; alert(1); "')

# Streamlit host: demo button embeds the review app
at = AppTest.from_file("../app.py", default_timeout=60).run()
assert not at.exception, at.exception
toggle = at.get("iframe")[0].proto.srcdoc  # landing page carries the theme toggle, sharing the review's saved choice
assert 'id="t"' in toggle and '"dejavu:theme"' in toggle and "/*__THEME__*/" not in toggle
next(x for x in at.button if x.label == "Try the demo set").click().run()
assert not at.exception, at.exception
iframe = at.get("iframe")[0].proto
assert "const DATA = {" in iframe.srcdoc and "grid_bfs/ai_rewrite.java" in iframe.srcdoc
print("APP PASS")
