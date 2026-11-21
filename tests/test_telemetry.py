"""Telemetry checks. Run from repo root: .venv\\Scripts\\python -m tests.test_telemetry
Nothing is sent: urlopen is replaced, so this also runs in CI without a token."""
import json
import os
import urllib.request

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
print("TELEMETRY PASS")
