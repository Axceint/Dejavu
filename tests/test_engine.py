"""Run from repo root: .venv\\Scripts\\python -m tests.test_engine"""
import tempfile
from pathlib import Path

from dejavu.engine import scan, tokens

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
    assert ai - trap_x > 0.1, f"{ext}: AI rewrite should clearly outrank independent solution"
assert not any(p["a"].rsplit(".")[-1] != p["b"].rsplit(".")[-1] for p in res["pairs"]), "same-language only"
# AI rewrites often move functions into `class Solution`: the `self` plumbing must not hide the copy
ORIG = (Path(__file__).parent / "fixtures" / "orig.py").read_text()
WRAPPED = "class Solution:\n" + ORIG.split("\n\n\nnums")[0].replace("\n", "\n    ").replace("    \n", "\n") \
    .replace("def is_prime(n)", "    def is_prime(self, n)").replace("def solve(nums)", "def solve(self, nums)") \
    .replace("if is_prime(", "if self.is_prime(") + "\n\n\nnums = list(map(int, input().split()))\nc, t = Solution().solve(nums)\nprint(c, t)\n"
compile(WRAPPED, "wrapped", "exec")
with tempfile.TemporaryDirectory() as d:
    Path(d, "orig.py").write_text(ORIG)
    Path(d, "wrapped.py").write_text(WRAPPED)
    wrapped = scan(d)["pairs"][0]["score"]
print(f"class-wrapped copy {wrapped:.3f}")
assert wrapped > 0.85, "a copy moved into a class should still score near an exact copy"
assert ("LOOP", 3) in tokens("class S:\n    def go(self, n):\n        return self.go(n - 1)\n", "python"), "self.go() recursion"
assert ("LOOP", 1) in tokens("struct S { int go(int n) { return this->go(n - 1); } };", "cpp"), "this->go() recursion"
top = res["pairs"][0]
assert top["matches"] and all(len(m) == 2 for m in top["matches"]), "top pair needs line matches"
print("ALL PASS")
