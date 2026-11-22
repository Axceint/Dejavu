"""Odd inputs a hidden test set may contain. Run from repo root: .venv\\Scripts\\python -m tests.test_edge_cases"""
import re
import tempfile
import time
import zipfile
from pathlib import Path

from dejavu import engine
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
# Java and C++ grammars reject variation selectors and Hangul fillers inside names: a copy dropped to 0.73-0.75.
junk = "".join(map(chr, (0xFE01, 0xFE02, 0x3164)))
for ext in ("java", "cpp"):
    src = (Path(__file__).parent / "fixtures" / f"orig.{ext}").read_text()
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / f"a.{ext}").write_text(re.sub(r"(?<=[A-Za-z])[(]", junk + "(", src), "utf-8")
        (Path(d) / f"b.{ext}").write_text(src, "utf-8")
        r = scan(d)
        assert list(r["flags"]) == [f"a.{ext}"] and r["pairs"][0]["score"] > 0.99, (ext, r["pairs"][0]["score"])

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

with tempfile.TemporaryDirectory() as d:  # a tiny zip can unpack to a huge file: refuse it, don't parse it
    big = "x = y + 1\n" * 200_000
    with zipfile.ZipFile(Path(d, "bomb.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("big.py", big)
    Path(d, "dir").mkdir()
    Path(d, "dir", "big.py").write_text(big)
    for p in (Path(d, "bomb.zip"), Path(d, "dir")):
        try:
            scan(p)
            raise AssertionError(f"oversized file in {p.name} must raise")
        except ValueError as e:
            assert "big.py" in str(e), e

def refused(path, why, base=None, want=""):
    try:
        scan(path, base)
    except ValueError as e:
        assert want in str(e), e
        return
    raise AssertionError(f"{why} must raise ValueError")


with tempfile.TemporaryDirectory() as d:  # inputs that would stall the shared server or silently find nothing
    d = Path(d)
    def zipped(name, entries):
        with zipfile.ZipFile(d / name, "w", zipfile.ZIP_DEFLATED) as z:
            for n, s in entries:
                z.writestr(n, s)
        return d / name

    # many tiny files: pairs grow with the square of the count
    refused(zipped("many.zip", [(f"s{i}.py", "x = 1\n") for i in range(engine.MAX_FILES + 1)]), "too many files", want="files")
    # many files each under the per-file cap still add up
    refused(zipped("total.zip", [(f"s{i}.py", "x = 1\n" * 150_000) for i in range(engine.MAX_TOTAL // 900_000 + 1)]),
            "too many bytes in total", want="MB")
    # a single-file starter skipped the per-file cap
    (d / "starter.py").write_text("x = 1\n" * 200_000)
    refused(zipped("ok.zip", [("a.py", ORIG), ("b.py", ORIG)]), "oversized starter", base=d / "starter.py", want="starter.py")
    # an LMS export (zip of per-student zips) or the wrong language used to show a clean "no copies" result
    inner = zipped("inner.zip", [("main.py", ORIG)]).read_bytes()
    refused(zipped("nested.zip", [("s1.zip", inner), ("s2.zip", inner)]), "zip of zips", want=".zip")
    refused(zipped("c.zip", [("a.c", "int main(){}"), ("b.c", "int main(){}")]), "no supported files", want=".c")
    # damaged compressed data inside an entry raised zlib.error, which the app didn't catch
    p = d / "damaged.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("a.py", ORIG * 50)
        z.writestr("b.py", ORIG * 50)
    b = bytearray(p.read_bytes())
    start = 30 + int.from_bytes(b[26:28], "little")  # first entry's data, after its local header
    b[start + 5:start + 40] = bytes(x ^ 0x5A for x in b[start + 5:start + 40])
    p.write_bytes(b)
    refused(p, "damaged entry", want="a.py")

with tempfile.TemporaryDirectory() as d:  # LMS layout: one folder per student, some students hand in several files
    sub = Path(d, "hw1.zip")
    with zipfile.ZipFile(sub, "w") as z:  # one wrapper folder around all students, as zips usually have
        for f in ("s1/main.py", "s1/util.py", "s2/main.py", "loose.py"):
            z.writestr("hw1/" + f, ORIG)
    assert pair(scan(sub), "hw1/s1/main.py", "hw1/s1/util.py") > 0.99, "off by default: folders can be assignments (demo)"
    r = scan(sub, by_folder=True)
    assert pair(r, "hw1/s1/main.py", "hw1/s1/util.py") == 0, "one student's own files are not a copy"
    assert pair(r, "hw1/s1/util.py", "hw1/s2/main.py") > 0.99, "across students still counts"
    assert pair(r, "hw1/loose.py", "hw1/s1/main.py") > 0.99, "a file outside any student folder is its own submission"

scan_marks = lambda p: (lambda r: next(iter(r["marks"].values()), []))(scan(p))

with tempfile.TemporaryDirectory() as d:  # PowerShell 5's `>` and Notepad's "Unicode" save UTF-16: a copy scored 0
    d = Path(d)
    with zipfile.ZipFile(d / "u.zip", "w") as z:
        z.writestr("a.py", ORIG)
        z.writestr("le.py", ORIG.encode("utf-16"))  # little-endian with BOM, as Windows writes it
        z.writestr("be.py", "﻿".encode("utf-16-be") + ORIG.encode("utf-16-be"))
    r = scan(d / "u.zip")
    assert pair(r, "a.py", "le.py") > 0.99 and pair(r, "a.py", "be.py") > 0.99, "UTF-16 copies must match"
    assert not r["flags"], f"a BOM is not a hidden character: {r['flags']}"
    with zipfile.ZipFile(d / "crlf.zip", "w") as z:  # a zip made on Windows keeps CRLF; \r hid the fence watermark
        z.writestr("a.py", "```\r\n" + ORIG.replace("\n", "\r\n"))
    assert [m["kind"] for m in scan_marks(d / "crlf.zip")] == ["chat code fence"], "CRLF must not hide watermarks"
    (d / "dir").mkdir()
    (d / "dir" / "a.py").write_text(ORIG)
    (d / "dir" / "b.py").write_bytes(ORIG.encode("utf-16"))
    assert pair(scan(d / "dir"), "a.py", "b.py") > 0.99, "UTF-16 in a folder must match"
    (d / "base.py").write_bytes(ORIG.encode("utf-16"))  # starter saved as UTF-16 must still be subtracted
    assert pair(scan(d / "dir", base=d / "base.py"), "a.py", "b.py") < 0.1, "UTF-16 starter must be ignored in scoring"

try:
    scan("does/not/exist")
    raise AssertionError("missing path must raise")
except FileNotFoundError:
    pass

print("EDGE CASES PASS")
