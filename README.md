# Dejavu: AI-rewritten code plagiarism detector

Code Fuzion 2026 · Problem H1. Team: Himu, Akshit.

Dejavu takes a batch of Python, C++ and Java submissions and ranks every pair by how likely the two share an original solution. It still catches copies after variables are renamed, functions are reordered, loops become recursion, or an AI rewrites the code. It does this by comparing **code structure, not text**, and it needs no LLM: 300 submissions take about 1–2 seconds on a laptop.

**Live demo:** _link added after deploy (issue #4)_

## The idea in one example

Two students hand in these. Student B renamed everything to hide the copy:

```python
# Student A                      # Student B
def total(nums):                 def add_all(values):
    s = 0                            result = 0
    for x in nums:                   for v in values:
        s += x                           result += v
    return s                         return result
```

Dejavu first erases the disguise. Every name becomes `ID`, every number `LIT`, every loop `LOOP`. This is the real output for both files:

```
A: def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID
B: def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID
```

The renaming is gone. Next, Dejavu cuts each file into overlapping 6-word pieces and counts how many pieces two files share. Rare pieces count more than pieces everyone writes. It does this for every pair and shows the highest scores first. The rest of this README is the detail.

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
| Set of 6-token fingerprints (order ignored) | Reordered functions |
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

## Hidden characters

Code copied out of a chat window or a web page sometimes carries characters you can't see:

- zero-width spaces
- odd spaces such as the no-break space
- bidirectional controls that make code display differently from how it runs ("Trojan Source")
- look-alike letters, such as a Cyrillic `а` inside an English word
- blank Hangul filler letters and variation selectors, which pass as part of a name and can carry hidden bytes

Dejavu does two things with them:

1. **Flags them.** Each affected file is listed with the line and character, under `flags` in the result and as a `hidden chars` line in the CLI. This is a **hint, not proof** of AI use or copying.
2. **Removes them before comparing.** A single zero-width space after `def` broke parsing of a whole function and dropped a copy's score from 1.0 to 0.89 in our test, so hidden characters can't be used to hide a copy.

Not flagged: a byte-order mark at the start of a file (normal on Windows), comments written in another script (e.g. Russian), accented letters, and the one variation selector an emoji uses to pick its style.

## AI watermarks

Traces a chat tool or code assistant leaves in the file itself, listed under `marks` in the result, as an `AI watermark` line in the CLI, and as a tag, a fact and a gutter mark in the review screen:

- **AI attribution**: `# Generated by ChatGPT`, `written with GitHub Copilot`, `As an AI language model`, `Co-authored-by: Claude`
- **LLM control tokens**: `<|endoftext|>`, `<|im_start|>`
- **Chat code fence**: a markdown fence (```` ```python ````) as the first or last line, left when a whole chat answer is pasted
- **Hidden text**: invisible Unicode tag letters ("ASCII smuggling") or a run of variation selectors, decoded back to the message they carry

Like hidden characters, a watermark is a **hint, not proof**, and never changes a score. Statistical watermarks (SynthID, green-list tokens) need the vendor's secret key, so Dejavu does not claim to find those. The demo set has one visible and one hidden watermark; `tests.test_watermark` and the 300-file `bench` check every kind and that clean files stay unmarked.

Scores are similarity scores for **ranking**, not probabilities. A high score means "look at this pair first", not "proven plagiarism".

## Run it

Needs Python 3.12 (tree-sitter has no wheels for 3.15 yet).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m dejavu scan path\to\submissions --top 20 --json result.json
```

Input is a folder or a `.zip`. Language comes from the extension: `.py`, `.java`, `.cpp .cc .cxx .h .hpp`.

**Starter code:** if every student got the same template, pass it with `--base starter.py` (a file, folder or `.zip`). Any code found in it is ignored. In our test, two independent solutions sharing a template scored 0.488 without `--base` and 0.011 with it.

From Python:

```python
from dejavu.engine import scan
result = scan("submissions.zip", base="starter.py")  # base is optional
# {"files": {name: source}, "seconds": float,
#  "pairs": [{"a", "b", "score", "matches": [[[a_start, a_end], [b_start, b_end]], ...]}],
#  "flags": {name: [{"line", "char", "name"}, ...]},   # only files with hidden characters
#  "marks": {name: [{"line", "kind", "text"}, ...]}}   # only files with AI watermarks
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

## How Dejavu compares to existing tools

Universities have used MOSS, JPlag and Dolos for years. They all compare structure instead of raw text, and Dejavu follows the same idea. What it adds is aimed at AI rewrites.

| | [MOSS](https://theory.stanford.edu/~aiken/moss) | [JPlag](https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a.html) | [Dolos](https://arxiv.org/abs/2402.10853) | **Dejavu** |
|---|---|---|---|---|
| Reads code as | Token fingerprints (winnowing) | Token stream (Greedy String Tiling) | tree-sitter syntax tree + fingerprints (winnowing) | tree-sitter syntax tree + every fingerprint |
| Renames | Ignored | Ignored | Ignored | Ignored |
| Loop ↔ recursion | No rule we found | No rule we found | No rule we found | **Both become `LOOP`** |
| Style-only rewrites (`++i`/`i++`, braces, `const`) | Partly | Partly | Partly | **Normalized** |
| Code everyone writes | Hides passages found in more than N files (`-m`) | Base-code option | See its docs | **Rarity weighting**: shared rare code counts more |
| Instructor template code | Base file (`-b`) | Base code (`-bc`) | See its docs | **Base code (`--base`)** |
| Hidden characters | Not documented | Not documented | Not documented | **Flagged and removed** |
| AI watermarks (attribution, hidden text) | Not documented | Not documented | Not documented | **Flagged, hidden text decoded** |
| Runs | Stanford web service | Java, local | Node.js, local or web | Python, local or web app |

"No rule we found" and "Not documented" mean we didn't find the feature in the tool's papers or docs. It doesn't mean we tested the tool.

## Limitations

- Only files in the same language are compared, so a Python solution translated into Java is not caught.
- The test set is small (3 problems) and hand-written. Thresholds may need tuning on the real data.
- A heavy rewrite that changes the algorithm itself, such as a hash map replaced by sorting, is treated as a different solution. That is by design.

## AI-use disclosure

Claude Code (Anthropic) and Codex (OpenAI) assisted with planning, code and tests, and the team reviewed and ran everything. **Detection uses no LLM:** every score comes from the structural comparison described above.
