"""Streamlit UI and evidence smoke test. Run from repo root: .venv\\Scripts\\python -m tests.test_app"""
from streamlit.testing.v1 import AppTest

from dejavu.explain import verbatim

# verbatim: rare identical lines count, boilerplate shared by 3+ files does not
a = "x = 1\n    long long weird_total = 0; // tally\n    int helper_value = 42;\n"
b = "y = 2\n    int helper_value = 42;\n    long long weird_total = 0; // tally\n"
assert verbatim(a, b) == [(2, 3, "long long weird_total = 0; // tally"), (3, 2, "int helper_value = 42;")]
assert verbatim(a, b, {"int helper_value = 42;"}) == [(2, 3, "long long weird_total = 0; // tally")]

at = AppTest.from_file("../app.py", default_timeout=60).run()
assert not at.exception, at.exception
next(b for b in at.button if b.label == "Try the demo set").click().run()
assert not at.exception, at.exception

top = at.dataframe[0].value.head(6)
kind = lambda f: f.split("/")[1].split(".")[0]
assert all({kind(a), kind(b)} == {"orig", "ai_rewrite"} for a, b in zip(top["File A"], top["File B"])), top

evidence = " ".join(m.value for m in at.markdown)
assert "names fill the same roles" in evidence and "`distance` → `dist`" in evidence, evidence

body = next(h.proto.body for h in at.get("html") if 'class="src"' in h.proto.body)  # file A of the top pair
assert "ln hot" in body, "top pair shows highlighted matched lines"
assert "&lt;" in body and "<int" not in body, "submission code must be HTML-escaped"
print("APP PASS")
