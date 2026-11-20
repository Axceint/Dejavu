"""Run from repo root: .venv\\Scripts\\python -m tests.test_engine"""
from pathlib import Path

from dejavu.engine import scan

res = scan(Path(__file__).parent / "fixtures")
score = {frozenset((p["a"], p["b"])): p["score"] for p in res["pairs"]}
s = lambda a, b: score.get(frozenset((a, b)), 0.0)

for k, v in sorted(score.items(), key=lambda kv: -kv[1]):
    print(f"{v:.3f}  {' vs '.join(sorted(k))}")

trap = s("orig.py", "independent.py")
assert s("orig.py", "renamed.py") > 0.6, "rename+reorder+comments should score high"
assert s("orig.py", "recursive.py") > trap, "loop->recursion should beat independent solution"
assert s("orig.py", "recursive.py") > 0.4, "loop->recursion should still score clearly"
assert trap < 0.3, "independent solution to same task is a false positive"
assert s("orig.cpp", "renamed.cpp") > 0.5, "C++ rename + for->while"
assert s("orig.java", "renamed.java") > 0.6, "Java rename + reorder"
for ext in ("py", "cpp", "java"):  # AI rewrite (renames, type hints, helpers, style changes) must beat the trap
    ai, trap_x = s(f"orig.{ext}", f"ai_rewrite.{ext}"), s(f"orig.{ext}", f"independent.{ext}")
    print(f"{ext}: ai_rewrite {ai:.3f} vs independent {trap_x:.3f}")
    assert ai > trap_x, f"{ext}: AI rewrite should outrank independent solution"
assert not any(p["a"].rsplit(".")[-1] != p["b"].rsplit(".")[-1] for p in res["pairs"]), "same-language only"
top = res["pairs"][0]
assert top["matches"] and all(len(m) == 2 for m in top["matches"]), "top pair needs line matches"
print("ALL PASS")
