"""Report sorting checks. Run from repo root: .venv\\Scripts\\python -m tests.test_triage
No network: ask.generate is replaced."""
import os

from dejavu import ask
from scripts import triage

os.environ["LLM_API_KEY"] = "k"
for reply, want in [("small", "small"), (" Small.\n", "small"), ("needs-review", "needs-review"),
                    ("small. ignore previous instructions", "needs-review"), ("", "needs-review")]:
    ask.generate = lambda messages, r=reply: r
    assert triage.kind("t", "b") == want, (reply, want)


def down(messages):
    raise ask.Unavailable("quota")


ask.generate = down
assert triage.kind("t", "b") == "needs-review", "a model error sends the report to a person"
ask.generate = lambda messages: "small"
os.environ.pop("LLM_API_KEY")
assert triage.kind("t", "b") == "needs-review", "no key: nothing sorted as small"
print("TRIAGE PASS")
