# Handover: Himu → Akshit

The engine is done and tested. What's left is everything people **see**: the web UI, the hosted link and the demo. This file covers what you need to start. Team decisions live in [STATUS.md](STATUS.md); how the engine works is in [README.md](README.md).

## 1. Get running (about 5 min)

```powershell
cd C:\aelprojs\dejavu
git switch main; git pull
py -3.12 -m venv .venv                      # must be 3.12: tree-sitter has no 3.15 wheels
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m dejavu scan tests\problems --top 8
```

It works if the top 6 lines are the 6 `orig` vs `ai_rewrite` pairs, and the run finishes in under a second.

## 2. What already works

| Piece | Where | Proof |
|---|---|---|
| Engine: Python/C++/Java, renames, reorder, loop↔recursion, AI-style rewrites | `dejavu/engine.py` | `python -m tests.test_engine` |
| Hidden-character flags (zero-width, look-alike letters…) | `hidden_chars()` | `python -m tests.test_edge_cases` |
| Starter-code exclusion (`base=`) | `scan(path, base)` | same |
| 300 files in about 1 s (limit is 2 min) | | `python -m tests.bench` |
| CLI | `python -m dejavu scan <folder/zip> [--base starter.py] [--json out.json]` | |
| CI runs all 4 test suites on every PR | `.github/workflows/test.yml` | Actions tab |

## 3. The one function you call

```python
from dejavu.engine import scan
r = scan("submissions.zip", base=None)    # folder or .zip; base = optional starter code
r["files"]   # {name: source_text}
r["pairs"]   # [{"a": name, "b": name, "score": 0..1, "matches": [[[a0, a1], [b0, b1]], ...]}], best first
r["flags"]   # {name: [{"line": 3, "char": "U+200B", "name": "ZERO WIDTH SPACE"}]}  (only files with hidden chars)
r["seconds"] # float
```

- `matches` holds 1-based, inclusive line ranges: lines a0–a1 in file `a` match lines b0–b1 in file `b`. It's filled for the **top 100 pairs only**; lower pairs get `[]`.
- Only same-language pairs appear. A pair with no shared code isn't listed at all.
- To work offline with fake data: `json.load(open("sample_result.json"))` has the same shape.
- Errors to show nicely: `FileNotFoundError` (bad path) and `ValueError` (the base has no .py/.cpp/.java code).

## 4. Your tasks, in order

### Task 1: Streamlit UI (issue #3, about 2–3 h)

Create `app.py` at the repo root. Run it with `.venv\Scripts\streamlit run app.py`.

1. **Upload:** `st.file_uploader` for one `.zip` of submissions, plus an optional starter-code file. Save the zip to a `tempfile` folder and call `scan()`.
2. **"Try the demo set" button:** run `scan("tests/problems")`. Judges can then see results without a zip of their own. Highest value for least work.
3. **Ranked table:** rank, score, file A, file B, plus a ⚠ marker when either file appears in `r["flags"]`.
4. **Side-by-side view:** pick a pair, show both files next to each other (`st.columns(2)`) with line numbers, and highlight the matched line ranges from `matches`.
   - `st.code` can't highlight lines. Build the HTML yourself and render it with `st.html`.
   - **Escape the code with `html.escape()` first.** Submissions are untrusted, so unescaped code can inject HTML or scripts into the page.
5. **Flags panel:** for the selected files, list the hidden characters with their line numbers. Word it as "hint, not proof".

Done when: the demo set shows the 6 true pairs on top, clicking one highlights the right lines on both sides, and a 300-file zip finishes in well under 2 minutes.

### Task 2: Deploy (issue #4, about 30 min)

1. Go to share.streamlit.io → New app → repo `Axceint/Dejavu`, branch `main`, main file `app.py`.
2. Under Advanced settings, set **Python 3.12**.
3. Open the URL, click "Try the demo set" and check that it works.
4. Put the URL in `README.md` (the `**Live demo:**` line) via a PR.

Watch for: the first scan on a fresh server can be slower while tree-sitter sets up its parsers. CI on Linux already installs from `requirements.txt` cleanly.

### Task 3: UX polish (only once 1 and 2 work)

Ranked by value:

1. Use "review first" wording, never "plagiarised". Scores rank pairs; they aren't proof (README says why).
2. Score bands by colour, for example ≥0.4 red, 0.2–0.4 amber, else grey. These are rough cut-offs from our test set, so label them that way.
3. "Download results" button (`st.download_button` with the JSON or a CSV of the pairs).
4. A short "How it works" expander. Copy "The idea in one example" from the README.

### Hold time for the hour-12 change

The organisers announce a requirement change at hour 12. Nobody knows it yet, so keep about 5 hours free and don't guess it in advance.

## 5. How we ship (same rules for both of us)

1. Create an issue and add it to the [board](https://github.com/users/itzhimanshugt/projects/4).
2. Branch `akshit/<topic>` from fresh `main`. **Never push to `main`.**
3. Before pushing, run all 4 tests: `test_engine`, `test_edge_cases`, `test_problems`, `bench`.
4. Open a PR with `Closes #N`, wait for the green CI check, then squash-merge.

If you use Claude Code, the repo skill `.claude/skills/ship/SKILL.md` already does this. Swap `himu/` for `akshit/`.

Gotchas we hit:
- **Windows PowerShell 5.1:** `Set-Content` and `Get-Content` corrupt UTF-8 files. Edit files in your editor.
- **Python version:** use 3.12, not 3.15.
- **Engine changes:** if you need the engine to return something new, open an issue and tag Himu, so the UI and engine don't change the same file at once.

## 6. The 3-minute demo for mentors and judges

1. Open the hosted app → "Try the demo set". The 6 real copies rank on top.
2. Click the top pair: matched logic is highlighted side by side, despite the renames.
3. Explain the idea: names become `ID`, loops become `LOOP`, rare shared pieces count most.
4. Run `python -m tests.bench`: 300 files in about 1 s.
5. Name the honest limits from the README: cross-language copies aren't caught, the test set is hand-made, and a score is a ranking, not proof.
