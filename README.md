# Dejavu: AI-rewritten code plagiarism detector

Code Fuzion 2026 · Problem H1. Team: Himu, Akshit.

Dejavu takes a batch of Python, C++ and Java submissions and ranks every pair by how likely the two share an original solution. It still catches copies after variables are renamed, functions are reordered, loops become recursion, or an AI rewrites the code. It does this by comparing **code structure, not text**, and it needs no LLM: 300 submissions take about 1–2 seconds on a laptop.

**Live demo:** _link added after deploy (issue #4)_

## How it works

```
submissions (folder or .zip)
  → parse each file into a syntax tree (tree-sitter, all 3 languages)
  → normalize: names → ID, literals → LIT, comments/qualifiers/braces dropped,
               for/while loops and self-recursive calls → LOOP, ++x/x++ → UPD
  → fingerprint: hash every run of 5 normalized tokens
  → score each same-language pair by shared fingerprints, weighted by rarity
  → ranked pairs + the matching line ranges for a side-by-side view
```

**Why each step:**

| Step | What it defeats |
|---|---|
| Syntax tree instead of raw text | Formatting, whitespace, comments |
| Names → `ID`, types → `ID` | Variable/function renames, `int` → `long` |
| Loops and self-calls → `LOOP` | Loop ↔ recursion rewrites |
| Drop braces, `;`, `const`/`static`/`final`, unify `++x`/`x++` | Style-only AI rewrites |
| Set of 5-token fingerprints (order ignored) | Reordered functions |
| **Rarity weighting** (fingerprint in 3 files counts far more than one in 150) | False positives from code *everyone* writes for the same task (input reading, standard loops) |
| Score = average of Jaccard (shared ÷ total) and containment (shared ÷ smaller file, floored at half the bigger file) | Copies padded with extra code, without letting a tiny boilerplate file look "fully contained" |

**Why no LLM:** 300 submissions make about 45,000 pairs. An LLM call per pair would be slow, costly and give different answers on different runs. Dejavu is deterministic (stable `crc32` hashes), so the same input always gives the same ranking.

## Results

From the repo's own tests (`tests/`). The test files were written by hand, the "AI rewrites" included, in the style AI tools produce: renamed identifiers, type hints and docstrings, extracted helpers, guard clauses, different library calls. They are a sanity check, not a benchmark.

**Original vs. rewrite** (prime counting):

| Rewrite | Python | C++ | Java |
|---|---|---|---|
| Renamed + reordered functions + comments | 0.754 | 0.678 | 0.896 |
| Loop → recursion | 0.550 | | |
| AI-style rewrite | 0.244 | 0.399 | 0.555 |
| *Independent solution, same task (should be low)* | *0.031* | *0.234* | *0.216* |

**Ranking across problems** (two_sum + grid_bfs scanned together): in every language, each AI rewrite ranks above **every** false pair (independent solutions and cross-problem pairs).

| Language | AI rewrite scores | Highest false pair |
|---|---|---|
| Python | 0.233 – 0.470 | 0.173 |
| C++ | 0.254 – 0.402 | 0.179 |
| Java | 0.486 – 0.643 | 0.202 |

**Speed:** 300 files (worst case, nearly every pair overlapping) in about 1–2 s. The limit is 2 minutes.

**Odd inputs handled:** empty and comment-only files, syntax errors, non-UTF-8 text, macOS zip junk (`__MACOSX/`, `._*`), exact duplicates (rank first), tiny boilerplate files, very large files.

Scores are similarity scores for **ranking**, not probabilities. A high score means "look at this pair first", not "proven plagiarism".

## Run it

Needs Python 3.12 (tree-sitter has no wheels for 3.15 yet).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m dejavu scan path\to\submissions --top 20 --json result.json
```

Input is a folder or a `.zip`. Language comes from the extension: `.py`, `.java`, `.cpp .cc .cxx .h .hpp`.

From Python:

```python
from dejavu.engine import scan
result = scan("submissions.zip")
# {"files": {name: source}, "seconds": float,
#  "pairs": [{"a", "b", "score", "matches": [[[a_start, a_end], [b_start, b_end]], ...]}]}
```

`matches` (1-based line ranges for the side-by-side view) is filled in for the top 100 pairs.

## Tests and CI

Every pull request and every push to `main` runs all four checks in GitHub Actions:

```powershell
.venv\Scripts\python -m tests.test_engine      # renames, reorder, loop->recursion, AI rewrite vs independent
.venv\Scripts\python -m tests.test_edge_cases  # odd inputs never crash or create false positives
.venv\Scripts\python -m tests.test_problems    # true pairs outrank all false pairs across problems
.venv\Scripts\python -m tests.bench            # 300 files under 2 minutes
```

Work is tracked in GitHub issues on a [project board](https://github.com/users/itzhimanshugt/projects/4). Each change is merged by PR only after CI passes.

## Limitations

- Only files in the same language are compared, so a Python solution translated into Java is not caught.
- The test set is small (3 problems) and hand-written. Thresholds may need tuning on the real data.
- A heavy rewrite that changes the algorithm itself, such as a hash map replaced by sorting, is treated as a different solution. That is by design.

## AI-use disclosure

Claude Code (Anthropic) and Codex (OpenAI) assisted with planning, code and tests, and the team reviewed and ran everything. **Detection uses no LLM:** every score comes from the structural comparison described above.
