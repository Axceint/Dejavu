# Dejavu â€“ team status (source of truth; Claude/Codex memory is NOT shared)

## Problem
Code Fuzion 2026 Â· H1 AI-Rewritten Code Plagiarism Detector. Rank Python/C++/Java submission pairs by likelihood of a shared original. Structural comparison, side-by-side view, 300 files < 2 min. No LLM per pair.

## Decisions
- Python 3.12 (tree-sitter has no 3.15 wheels). `py -3.12 -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt`.
- Engine: tree-sitter â†’ normalized tokens (namesâ†’ID, literalsâ†’LIT, loops/self-callsâ†’LOOP) â†’ winnowed k-gram fingerprints (stable hash) â†’ rarity-weighted overlap score. Pairs compared only within the same language.
- UI: Streamlit, hosted on Streamlit Community Cloud (set Python 3.12 in advanced settings).
- Input: folder or .zip of files; language from extension (.py / .cpp .cc .h .hpp / .java).
- Repo lives outside OneDrive (e.g. C:\dev\Dejavu). Branches `himu/*`, `akshit/*`; PRs into `main`.

## Engine interface (Akshit builds UI against this)
```python
from dejavu.engine import scan
result = scan("path/to/folder_or.zip")
# result = {"files": {name: source_text}, "seconds": float,
#           "pairs": [{"a": name, "b": name, "score": 0..1,
#                      "matches": [[[a_start, a_end], [b_start, b_end]], ...]}]}  # 1-based lines, sorted by score desc
```
Fake data to build against: `sample_result.json`.

## Owners
- Himu: engine + CLI (`python -m dejavu scan <path>`)
- Akshit: test dataset, Streamlit UI, side-by-side view, deploy, demo/slides
- Codex: PR review only

## Status
- [x] Setup, parsers verified
- [x] Engine + self-test (Himu): 300 files in ~2 s
- [ ] UI on fake data (Akshit)
- [ ] Hosted link by hour 12
- [ ] Hour-12 change: TBD (reserve hours 12â€“17)

## AI-use disclosure (for README)
Claude Code and Codex assisted with code. Detection scoring is pure structural comparison; no LLM is used in scoring.
