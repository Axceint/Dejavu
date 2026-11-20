"""Streamlit UI smoke test. Run from repo root: .venv\\Scripts\\python -m tests.test_app"""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app.py", default_timeout=60).run()
assert not at.exception, at.exception
next(b for b in at.button if b.label == "Try the demo set").click().run()
assert not at.exception, at.exception

top = at.dataframe[0].value.head(6)
kind = lambda f: f.split("/")[1].split(".")[0]
assert all({kind(a), kind(b)} == {"orig", "ai_rewrite"} for a, b in zip(top["file A"], top["file B"])), top

body = at.get("html")[0].proto.body  # file A of the top pair
assert "rgba(255,190,0" in body, "top pair shows highlighted matched lines"
assert "&lt;" in body and "<int" not in body, "submission code must be HTML-escaped"
print("APP PASS")
