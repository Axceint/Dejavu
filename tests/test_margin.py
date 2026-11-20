r"""Separation margin per language. Run from repo root: .venv\Scripts\python -m tests.test_margin

The margin is the weakest true copy's score minus the strongest false pair's score, over the demo problems plus
the prime fixtures. True = an original vs each of its copies (AI rewrite, rename, loop-to-recursion); copy vs copy
of the same original counts as neither; everything else in the same language is false. Bigger is better: a
positive margin means every copy outranks every unrelated pair.
"""
import shutil
import tempfile
from pathlib import Path

from dejavu.engine import scan

HERE = Path(__file__).parent
FLOOR = 0.04  # engine v2 measured py 0.064, cpp 0.045, java 0.218 (v1: 0.023, 0.027, 0.261)

with tempfile.TemporaryDirectory() as d:
    shutil.copytree(HERE / "problems", d, dirs_exist_ok=True)
    (Path(d) / "prime").mkdir()
    for p in (HERE / "fixtures").iterdir():
        if p.suffix in (".py", ".cpp", ".java"):
            shutil.copy(p, Path(d) / "prime" / p.name)
    r = scan(d)

score = {frozenset((p["a"], p["b"])): p["score"] for p in r["pairs"]}
ok = True
for ext in ("py", "cpp", "java"):
    names = [n for n in r["files"] if n.endswith("." + ext)]
    true, skip = set(), set()
    for prob in {n.split("/")[0] for n in names}:
        fam = [f"{prob}/{k}.{ext}" for k in ("orig", "ai_rewrite", "renamed", "recursive") if f"{prob}/{k}.{ext}" in r["files"]]
        true |= {frozenset((fam[0], c)) for c in fam[1:]}
        skip |= {frozenset((x, y)) for i, x in enumerate(fam[1:]) for y in fam[i + 2:]}
    weakest = min(score.get(k, 0.0) for k in true)
    falsest = max((v for k, v in score.items() if k not in true | skip and next(iter(k)).endswith("." + ext)), default=0.0)
    ok &= weakest - falsest >= FLOOR
    print(f"{ext:4} weakest copy {weakest:.3f} | strongest false pair {falsest:.3f} | margin {weakest - falsest:+.3f}")
assert ok, f"a language's separation margin fell below {FLOOR}"
print("MARGIN PASS")
