"""Odd inputs a hidden test set may contain. Run from repo root: .venv\\Scripts\\python -m tests.test_edge_cases"""
import tempfile
import time
import zipfile
from pathlib import Path

from dejavu.engine import hidden_chars, scan

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

# Hidden characters: flagged per file, never part of the score. Written as escapes so editors can't drop them.
names = lambda src: [f["name"] for f in hidden_chars(src)]
assert names("x = 1\u200b\n") == ["ZERO WIDTH SPACE"]
assert names("a = 1\nb\u00a0= 2\n") == ["NO-BREAK SPACE"] and hidden_chars("a\nb\u00a0")[0]["line"] == 2
assert names("s = '\u202e'\n") == ["RIGHT-TO-LEFT OVERRIDE"], "bidi control (Trojan Source)"
assert names("d\u0430ta = 1\n") == ["CYRILLIC SMALL LETTER A in 'd\u0430ta'"], "Latin+Cyrillic look-alike word"
assert names("x\u3164 = 1\n") == ["HANGUL FILLER"], "blank letter that passes as part of a name"
assert names("x = 1  # " + "".join(chr(0xE0000 + ord(c)) for c in "hi")) == ["TAG CHARACTER x2"], "one flag per tag run"
assert names("x = 1  # \ufe01\ufe02\ufe03\n") == ["VARIATION SELECTOR-2 x3"], "variation-selector run hides bytes"
assert names("y\ufe0f = 1\n") == ["VARIATION SELECTOR-16"], "a selector on a letter selects nothing"
# Not flagged: leading BOM, a Russian comment, accented letters, bytes replaced while decoding, an emoji's selector.
for clean in ("\ufeffx = 1\n", "# \u043f\u0440\u0438\u0432\u0435\u0442 world\n", "x = '\u00e9\ufffd'\n",
              "s = '\u26a0\ufe0f'\n"):
    assert hidden_chars(clean) == [], f"false flag on {clean!r}"
with tempfile.TemporaryDirectory() as d:
    (Path(d) / "a.py").write_text(ORIG.replace("\n", "\u200b\n", 1), "utf-8")
    (Path(d) / "b.py").write_text(ORIG, "utf-8")
    r = scan(d)
    assert list(r["flags"]) == ["a.py"] and r["pairs"][0]["score"] > 0.99, "flagged, and the hidden char cannot hide the copy"

# Starter code: two independent solutions that both include the same instructor template look like copies until
# the template is passed as base.
TEMPLATE = (Path(__file__).parent / "problems" / "grid_bfs" / "orig.py").read_text()
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    (d / "subs").mkdir()
    (d / "subs" / "a.py").write_text(TEMPLATE + "\n" + ORIG)
    (d / "subs" / "b.py").write_text(TEMPLATE + "\n" + (Path(__file__).parent / "fixtures" / "independent.py").read_text())
    (d / "starter.py").write_text(TEMPLATE)
    without = pair(scan(d / "subs"), "a.py", "b.py")
    with_base = pair(scan(d / "subs", base=d / "starter.py"), "a.py", "b.py")
    print(f"shared template: {without:.3f} without base, {with_base:.3f} with base")
    assert without > 0.4 and with_base < 0.1, "base code must not make independent solutions look copied"
    (d / "notes.txt").write_text("hi")
    try:
        scan(d / "subs", base=d / "notes.txt")
        raise AssertionError("base without code must raise")
    except ValueError:
        pass

try:
    scan("does/not/exist")
    raise AssertionError("missing path must raise")
except FileNotFoundError:
    pass

print("EDGE CASES PASS")
