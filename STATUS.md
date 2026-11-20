# Dejavu - team status (source of truth; Claude/Codex memory is NOT shared)

## Problem
Code Fuzion 2026 · H1 AI-Rewritten Code Plagiarism Detector. Rank Python/C++/Java submission pairs by likelihood of a shared original. Structural comparison, side-by-side view, 300 files < 2 min. No LLM per pair.

## Decisions
- Python 3.12 (tree-sitter has no 3.15 wheels). `py -3.12 -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt`.
- Engine: tree-sitter → normalized tokens (names→ID, literals→LIT, loops/self-calls→LOOP) → all 5-token k-gram fingerprints (stable crc32 hash) → rarity-weighted overlap score (avg of Jaccard + containment). Pairs compared only within the same language.
- UI: Streamlit, hosted on Streamlit Community Cloud (set Python 3.12 in advanced settings).
- Input: folder or .zip of files; language from extension (.py / .cpp .cc .h .hpp / .java).
- Repo lives outside OneDrive (e.g. C:\dev\Dejavu). Branches `himu/*`, `akshit/*`; PRs into `main`.
- Commits are authored by the human only (no AI co-author lines).

## Engine interface (Akshit builds UI against this)
```python
from dejavu.engine import scan
result = scan("path/to/folder_or.zip")
# result = {"files": {name: source_text}, "seconds": float,
#           "pairs": [{"a": name, "b": name, "score": 0..1,
#                      "matches": [[[a_start, a_end], [b_start, b_end]], ...]}],  # 1-based lines, sorted by score desc
#           "flags": {name: [{"line": n, "char": "U+200B", "name": "ZERO WIDTH SPACE"}]}}  # hidden chars; hint only, not in score
```
`matches` is filled for the top 100 pairs only. Fake data to build against: `sample_result.json`.

## Commands (repo root)
- Scan: `.venv\Scripts\python -m dejavu scan <folder_or_zip> --top 20 --json out.json`
- Self-test: `.venv\Scripts\python -m tests.test_engine`
- 300-file timing: `.venv\Scripts\python -m tests.bench`

## Owners
- Himu: engine + CLI
- Akshit: test dataset, Streamlit UI, side-by-side view, deploy, demo/slides
- Codex: PR review only

## Status
- [x] Setup, parsers verified
- [x] Engine + self-test (Himu): 300 files in ~2 s; rename/reorder 0.75, loop→recursion 0.55, independent same-task solution 0.04
- [ ] UI on fake data (Akshit)
- [ ] Hosted link by hour 12
- [ ] Hour-12 change: TBD (reserve hours 12–17)

## AI-use disclosure (for README)
Claude Code and Codex assisted with code. Detection scoring is pure structural comparison; no LLM is used in scoring.
