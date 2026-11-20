"""Odd inputs a hidden test set may contain. Run from repo root: .venv\\Scripts\\python -m tests.test_edge_cases"""
import tempfile
import time
import zipfile
from pathlib import Path

from dejavu.engine import scan

ORIG = (Path(__file__).parent / "fixtures" / "orig.py").read_text()
pair = lambda r, a, b: next((p["score"] for p in r["pairs"] if {p["a"], p["b"]} == {a, b}), 0.0)

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    files = {
        "orig.py": ORIG,
        "empty.py": "",
        "blank.py": "\n\n   \n",
        "comments.py": "# nothing here\n# at all\n",
        "broken.py": "def f(:\n    return [\n",
        "broken.cpp": "int main( { for (;; \n",
        "dup_a.py": ORIG,
        "dup_b.py": ORIG,
        "tiny.py": "nums = list(map(int, input().split()))\nprint(sum(nums))\n",
    }
    for name, text in files.items():
        (d / name).write_text(text)
    (d / "latin1.py").write_bytes(b"x = '\xe9\xe8'\nprint(x)\n")  # not valid UTF-8

    r = scan(d)
    assert len(r["files"]) == len(files) + 1, "every file loads, none crash"
    assert pair(r, "dup_a.py", "dup_b.py") > 0.99, "exact duplicates score ~1"
    assert r["pairs"][0]["score"] > 0.99, "duplicates rank first"
    for junk in ("empty.py", "blank.py", "comments.py", "broken.py"):
        assert pair(r, "orig.py", junk) < 0.3, f"{junk} must not look like a copy"
    assert pair(r, "orig.py", "tiny.py") < 0.3, "tiny boilerplate-only file must not look like a copy"

    # Zip: nested + uppercase paths count; macOS metadata junk is ignored.
    z = d / "subs.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("team1/Main.PY", ORIG)
        zf.writestr("team2/sol.py", ORIG)
        zf.writestr("__MACOSX/team1/._Main.PY", b"\x00\x05\x16\x07binary")
        zf.writestr("team3/._sol.py", b"\x00\x05\x16\x07binary")
    r = scan(z)
    assert set(r["files"]) == {"team1/Main.PY", "team2/sol.py"}, sorted(r["files"])

    # Very large file stays fast.
    big = d / "big"
    big.mkdir()
    (big / "a.py").write_text(ORIG * 2000)
    (big / "b.py").write_text(ORIG * 2000)
    t = time.perf_counter()
    scan(big)
    assert time.perf_counter() - t < 20, "48k-line files must not stall the run"

try:
    scan("does/not/exist")
    raise AssertionError("missing path must raise")
except FileNotFoundError:
    pass

print("EDGE CASES PASS")
