"""Telemetry checks. Run from repo root: .venv\\Scripts\\python -m tests.test_telemetry
Nothing is sent: urlopen is replaced, so this also runs in CI without a token."""
import io
import json
import os
import urllib.request
from pathlib import Path

from dejavu import ask, telemetry

secret = "zz_secret_name.py"
long_fn = "def f():\n" + "    x = 1\n" * (ask.SPAN + 5)  # one function longer than SPAN: cut into two chunks
files = {secret: long_fn, "b.py": "print('hello secret')\n"}

# Numbers only
s = telemetry.stats(files, 1.5)
assert all(isinstance(v, (int, float)) for v in s.values()), s
assert s["files"] == 2 and s["chunks_at_span"] == 1 and s["span"] == ask.SPAN, s

# Off without a token: no thread, nothing sent
os.environ.pop("GH_TELEMETRY_TOKEN", None)
assert telemetry.send(files, 1.5) is None

# With a token: one request, no code or file names in it, and a network failure stays silent
sent = []
def fake(req, timeout):
    sent.append(req.data.decode())
    raise OSError("offline")
urllib.request.urlopen = fake
telemetry.send(files, 1.5, token="t").join(5)
assert len(sent) == 1
assert "secret" not in sent[0] and "print" not in sent[0], sent[0]
body = json.loads(sent[0])["body"].strip("`json\n")
assert json.loads(body) == s, body
# In-app reports: fixed error texts, failures don't count toward the daily cap, and the text can't render markdown
calls, fail = [], False
def gh(req, timeout):
    calls.append(json.loads(req.data))
    if fail:
        raise OSError("boom server-detail")
    return io.BytesIO(b'{"number": 7}')
urllib.request.urlopen = gh
telemetry._sent.clear()
for bad in [("x", "Other", ""), ("  \n ", "Other", "t"), ("x", "Not a place", "t")]:
    try:
        telemetry.report(*bad)
        raise AssertionError(bad)
    except ValueError:
        pass
assert not calls, "nothing is sent without a token, text and a known place"
fail = True
try:
    telemetry.report("x", "Other", token="t")
    raise AssertionError("network failure must raise")
except ValueError as e:
    assert "boom" not in str(e), e
fail = False
assert telemetry._sent == [], "a failed send doesn't use up the cap"
evil = "see ``` @alice ![x](https://evil.test/a.png)\n" + "y" * 3000
assert telemetry.report(evil, "Ask AI", token="t") == 7
issue = calls[-1]
assert issue["body"].startswith(telemetry.MARK) and "\n````text\nsee ``` @alice" in issue["body"], issue["body"][:200]
assert issue["body"].endswith("\n````") and len(issue["body"]) < telemetry.MAX_CHARS + 200
assert issue["labels"] == ["bug", "from-app"] and "@alice" in issue["title"] and len(issue["title"]) < 100
for _ in range(telemetry.PER_DAY - 1):
    telemetry.report("x", "Other", token="t")
try:
    telemetry.report("x", "Other", token="t")
    raise AssertionError("over the daily cap")
except ValueError:
    pass
# the autofix workflow starts a fix only for issues that begin with this exact marker
assert telemetry.MARK in (Path(__file__).parent.parent / ".github/workflows/autofix.yml").read_text("utf-8")
print("TELEMETRY PASS")
