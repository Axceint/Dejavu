"""Ranking quality across problems. Run from repo root: .venv\\Scripts\\python -m tests.test_problems

Each problem folder has orig / ai_rewrite / independent in .py, .cpp, .java (grid_bfs also a renamed.py copy). The only true copy pair per
problem and language is orig vs ai_rewrite; every other pair (independent solutions, other problems) is false.
"""
from pathlib import Path

from dejavu.engine import scan

res = scan(Path(__file__).parent / "problems")
score = {frozenset((p["a"], p["b"])): p["score"] for p in res["pairs"]}
problems = sorted({n.split("/")[0] for n in res["files"]})
ok = True
for ext in ("py", "cpp", "java"):
    true = {frozenset((f"{p}/orig.{ext}", f"{p}/ai_rewrite.{ext}")) for p in problems}
    # renamed.* (a plain rename of orig, there so the demo shows a copy ring) is a copy too, never a false pair
    same = {frozenset((f"{p}/{x}.{ext}", f"{p}/renamed.{ext}")) for p in problems for x in ("orig", "ai_rewrite")}
    false_scores = [v for k, v in score.items() if k not in true | same and next(iter(k)).endswith("." + ext)]
    worst_false = max(false_scores, default=0.0)
    for p in problems:
        t = score.get(frozenset((f"{p}/orig.{ext}", f"{p}/ai_rewrite.{ext}")), 0.0)
        ind = score.get(frozenset((f"{p}/orig.{ext}", f"{p}/independent.{ext}")), 0.0)
        ranked_top = t > worst_false
        ok &= t > ind and ranked_top
        print(f"{ext:4} {p:9} ai_rewrite {t:.3f} | independent {ind:.3f} | worst false pair {worst_false:.3f}"
              f" | {'TOP' if ranked_top else 'not top'}")
assert ok, "an AI rewrite was outranked by an independent solution or a cross-problem pair"
print("PROBLEMS PASS")
