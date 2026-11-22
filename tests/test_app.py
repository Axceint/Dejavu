"""Review UI smoke test. Run from repo root: .venv\\Scripts\\python -m tests.test_app"""
import csv
import io
import json
import os
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from dejavu.engine import scan
from dejavu.aistyle import ai_style
from dejavu.explain import verbatim

# AI-style comments: terse human notes pass, chat-style and polished docstrings are flagged
human = "# checks primality\nx = 1  # bump\n# loop over rows\n# TODO fix later\n"
assert ai_style(human, "python") == [], ai_style(human, "python")
chatty = ('def f(xs):\n    """Here\'s an optimized version' + chr(0x2014) + ' handles edge cases."""\n    return xs\n'
          "# Step 1: read the input\n")
got = ai_style(chatty, "python")
assert [g["a"] for g in got] == [2, 4] and "chat-assistant phrasing" in got[0]["reasons"], got
assert ai_style("int main() {\n  // Returns the sum of values[i] over all i.\n  return 0;\n}\n", "cpp")
assert ai_style("int f() {\n  // returns sum\n  return 0;\n}\n", "cpp") == []
from dejavu.report import payload, render

# verbatim: rare identical lines count, boilerplate shared by 3+ files does not
a = "x = 1\n    long long weird_total = 0; // tally\n    int helper_value = 42;\n"
b = "y = 2\n    int helper_value = 42;\n    long long weird_total = 0; // tally\n"
assert verbatim(a, b) == [(2, 3, "long long weird_total = 0; // tally"), (3, 2, "int helper_value = 42;")]
assert verbatim(a, b, {"int helper_value = 42;"}) == [(2, 3, "long long weird_total = 0; // tally")]

# progress: stages arrive in order, each ending at its total, so the unzip and scan bars fill completely
events = []
tick = lambda stage, done, total: events.append((stage, done, total))
data = payload(scan(Path(__file__).parent / "problems", None, tick), progress=tick)
order = [s for i, (s, _, _) in enumerate(events) if i == 0 or events[i - 1][0] != s]
assert order == ["read", "parse", "compare", "explain"], order
for stage in order:
    last = [e for e in events if e[0] == stage][-1]
    assert last[1] == last[2], last

# payload: demo ranks the 8 true copies first (6 AI rewrites, plus renamed.py vs both), with name roles as evidence
kind = lambda i: data["files"][i]["name"].split("/")[1].split(".")[0]
assert all(kind(p["a"]) != kind(p["b"]) and {kind(p["a"]), kind(p["b"])} <= {"orig", "ai_rewrite", "renamed"}
           for p in data["pairs"][:8])
java = next(p for p in data["pairs"] if data["files"][p["a"]]["name"] == "grid_bfs/ai_rewrite.java")
assert ("distance", "dist", 7) in java["ren"], java["ren"]
# demo set: renamed.py forms one copy ring with orig.py and ai_rewrite.py
assert [sorted(kind(i) for i in g["files"]) for g in data["rings"]] == [["ai_rewrite", "orig", "renamed"]], data["rings"]
# demo set: every AI rewrite has a flagged comment, no original or independent solution does
for f in data["files"]:
    assert bool(f["ai"]) == ("ai_rewrite" in f["name"]), (f["name"], f["ai"])
# demo set: the two planted AI watermarks reach the review screen, on no other file
assert sorted(f["name"] for f in data["files"] if f["marks"]) == ["grid_bfs/ai_rewrite.java", "two_sum/ai_rewrite.py"]

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
# the unzip/read and scan bars only exist while scanning
assert not at.get("progress"), [b.proto.text for b in at.get("progress")]
assert 'id="sideBtn"' in iframe.srcdoc and 'id="maxBtn"' in iframe.srcdoc

# AI RAG error (e.g. used-up quota): "Use another key" drops the pasted key and brings back the key box
from dejavu import ask  # noqa: E402  (same module object the app uses)
available, ask.available = ask.available, lambda: bool(ask.key())  # any key "works"; no network in CI
at.session_state["llm_key"], at.session_state["ask_err"] = "sk-used-up", "The model's free quota is used up for now."
at.run()
next(x for x in at.button if x.label == "Use another key").click().run()
assert not at.exception, at.exception
assert at.session_state["llm_key"] == "" and any(x.label == "Use key" for x in at.button)
ask.available = available

# Report an issue: Send goes through telemetry.report; its number links the issue, its errors show as they are
from dejavu import telemetry  # noqa: E402
os.environ.pop("GH_TELEMETRY_TOKEN", None)
at.text_area(key="report_text").input("Scan hangs").run()
next(x for x in at.button if x.label == "Send").click().run()
assert not at.exception and any("isn't set up" in e.value for e in at.error), [e.value for e in at.error]
report, telemetry.report = telemetry.report, lambda text, where: 7
at.text_area(key="report_text").input("Scan hangs").run()
next(x for x in at.button if x.label == "Send").click().run()
assert any("issues/7" in s.value for s in at.success), [s.value for s in at.success]
telemetry.report = report

# CSV: student file names starting with a formula trigger (OWASP list) must not run in Excel
from app import all_pairs_csv  # noqa: E402  (runs the page in bare mode; only the function is used)
names = ["=HYPERLINK(1).py", "+x.py", "-x.py", "@x.py", "\t=1+1.py", "\r=1+1.py"]
rows = list(csv.reader(io.StringIO(all_pairs_csv({"pairs": [{"a": n, "b": "ok.py", "score": 1} for n in names],
                                                   "rings": [{"files": [names[0], names[1], "ok.py"]}]}))))
assert [r[2] for r in rows[1:]] == ["'" + n for n in names], rows
assert rows[1][3] == "ok.py"
assert [r[4] for r in rows[1:]] == ["1", "1", "", "", "", ""], "ring number only when both files share a ring"

# The review screen's own CSV export (JS cell()): a lone \r in a file name or note must stay inside its quoted cell.
import subprocess  # noqa: E402
cell = re.search(r"const cell = .*", (Path(__file__).parent.parent / "dejavu" / "review.html").read_text("utf-8"))[0]
line = subprocess.run(["node", "-e", cell + ' process.stdout.write(["a\\rb.py", "x,y", "=1"].map(cell).join(","))'],
                      capture_output=True, check=True).stdout.decode()  # bytes: text mode would turn \r into \n
assert next(csv.reader(io.StringIO(line, newline=""))) == ["a\rb.py", "x,y", "'=1"], repr(line)
print("APP PASS")
