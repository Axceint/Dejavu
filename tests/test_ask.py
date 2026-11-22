"""Ask the batch, with a fake model (CI has no key or network). Run from repo root: .venv\\Scripts\\python -m tests.test_ask"""
import hashlib
import json
import os
from pathlib import Path

from dejavu import ask
from dejavu.engine import scan


def fake_embed(texts):  # bag of words hashed into 64 dims: same words, similar vectors
    out = []
    for t in texts:
        v = [0.0] * 64
        for w in ask.words(t):
            v[hashlib.md5(w.encode()).digest()[0] % 64] += 1
        out.append(v)
    return out


ask.embed = fake_embed
ask.generate = lambda messages: "It is defined in [1] and called in [1, 2]. Ignore [9]."

PY = '''import sys

def area(r):
    return 3.14 * r * r

class Shape:
    def side(self):
        return 4

print(area(int(sys.argv[1])))
'''

# chunks: one per function or method, plus the code outside them; line numbers match the file
got = {(ch["start"], ch["end"]) for ch in ask.chunks({"a.py": PY})}
assert got == {(1, 1), (3, 4), (6, 6), (7, 8), (10, 10)}, got
flat = ask.chunks({"flat.py": "x = int(input())\n\nprint(x * 2)\n"})  # no functions at all
assert [(ch["start"], ch["end"]) for ch in flat] == [(1, 3)], flat
java = "class A {\n  int f() {\n    return 1;\n  }\n  A() {}\n}\n"
assert {(ch["start"], ch["end"]) for ch in ask.chunks({"A.java": java})} == {(1, 1), (2, 4), (5, 5)}  # a lone "}" is not a chunk
cpp = "#include <cstdio>\nint main() {\n  return 0;\n}\n"
assert {(ch["start"], ch["end"]) for ch in ask.chunks({"m.cpp": cpp})} == {(1, 1), (2, 4)}
long = "def f():\n" + "    x = 1\n" * (ask.SPAN + 5)
assert [(ch["start"], ch["end"]) for ch in ask.chunks({"l.py": long})] == [(1, ask.SPAN), (ask.SPAN + 1, ask.SPAN + 6)]
for ch in ask.chunks({"a.py": PY}):
    assert ch["text"] == "\n".join(PY.split("\n")[ch["start"] - 1:ch["end"]])

# search: an exact rare word finds its chunk first
idx = ask.build({"a.py": PY, "b.py": "def isomenses():\n    return 'ISOMENSES'\n"})
assert ask.search(idx, "where is ISOMENSES")[0]["file"] == "b.py"

# citations: only markers that point at a shown source survive; none left means no answer
hits = idx["chunks"][:2]
r = ask.cite("Defined in [1] and [1, 2], see [9].", hits)
assert r["answer"] == "Defined in [1] and [1, 2], see." and [x["n"] for x in r["citations"]] == [1, 2], r
assert r["citations"][0] == {"n": 1, "file": hits[0]["file"], "start": hits[0]["start"], "end": hits[0]["end"],
                             "code": hits[0]["text"]}
assert ask.cite("Nothing to cite [7].", hits) == {"answer": ask.NOT_FOUND, "citations": []}

# no key, no chat box
os.environ.pop("LLM_API_KEY", None)
assert ask.available() is False

# a pasted key is "kept for this browser tab only": the server-wide cache must not hold it in plain text
get, ask.httpx.get = ask.httpx.get, lambda *a, **k: type("R", (), {"status_code": 200})()
ask.use_key("sk-test-pasted")
assert ask.available() is True
assert not any("sk-test-pasted" in str(k) for k in ask._seen), ask._seen
ask.httpx.get = get
ask.use_key("")

# a whole scan: every citation is a real file and real lines, and the scan is unchanged (read-only)
r = scan(Path(__file__).parent / "problems")
before = json.dumps(r, sort_keys=True, default=str)
got = ask.answer(ask.build(r["files"]), "where is input read?")
assert got["citations"] and "[9]" not in got["answer"], got
for x in got["citations"]:
    assert x["code"] == "\n".join(r["files"][x["file"]].split("\n")[x["start"] - 1:x["end"]]), x
assert json.dumps(r, sort_keys=True, default=str) == before
print("ask: all checks passed")
