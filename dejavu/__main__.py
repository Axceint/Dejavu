import argparse
import json
import sys
from pathlib import Path

from .engine import scan

ap = argparse.ArgumentParser(prog="dejavu")
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("scan", help="rank similar submission pairs in a folder or .zip")
s.add_argument("path")
s.add_argument("--top", type=int, default=20)
s.add_argument("--json", help="write full result to this file")
args = ap.parse_args()

sys.stdout.reconfigure(errors="replace")  # Windows consoles can't print every character
r = scan(args.path)
for p in r["pairs"][: args.top]:
    print(f'{p["score"]:.3f}  {p["a"]}  vs  {p["b"]}')
for n, f in r["flags"].items():
    print(f'hidden chars  {n}: {len(f)} found, first on line {f[0]["line"]} ({f[0]["name"]})')
print(f'{len(r["files"])} files, {len(r["pairs"])} pairs with overlap, {r["seconds"]:.2f}s')
if args.json:
    Path(args.json).write_text(json.dumps(r), encoding="utf-8")
