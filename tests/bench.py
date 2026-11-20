"""300-file timing check. Run from repo root: .venv\\Scripts\\python -m tests.bench"""
import random
import re
import tempfile
from pathlib import Path

from dejavu.engine import scan

fixtures = Path(__file__).parent / "fixtures"
srcs = [p for p in fixtures.iterdir() if p.suffix in (".py", ".cpp", ".java")]
rng = random.Random(0)

with tempfile.TemporaryDirectory() as d:
    for i in range(300):
        src = srcs[i % len(srcs)]
        text = src.read_text()
        # Worst case: every file is a renamed copy, ~6x fixture size, so most pairs overlap.
        body = "\n".join(re.sub(r"\b(n|i|x|v|count|total)\b", f"v{rng.randint(0, 99)}", text) for _ in range(6))
        (Path(d) / f"s{i:03}{src.suffix}").write_text(body)
    r = scan(d)

print(f'{len(r["files"])} files, {len(r["pairs"])} pairs, {r["seconds"]:.2f}s')
assert len(r["files"]) == 300 and r["seconds"] < 120
print("BENCH PASS")
