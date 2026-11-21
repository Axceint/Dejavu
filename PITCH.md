# Dejavu: mentor and judge walkthrough

Read it top to bottom; each section is one thing to say. The technical detail lives in [README.md](README.md).

---

## 1. One-line pitch

> **"Dejavu finds students who copied code, even after an AI rewrote it to look different."**

---

## 2. The problem we solve

- A teacher or contest judge gets **300 code submissions** in Python, C++ and Java.
- Some students copied each other, then **asked an AI to rewrite** the copy so it looks new.
- No human can compare 300 files by hand: that's **~45,000 pairs**.
- **Dejavu lists the pairs to check first.** A human makes the final call.

---

## 3. Why it's hard

The AI changes how the code *looks*, not what it *does*:

- **Renames** variables: `total` → `add_all`
- **Reorders** functions
- **Swaps a loop for recursion**
- **Changes style:** braces, `++i` vs `i++`, comments
- **Adds noise:** docstrings, type hints, helper functions

A plain text compare fails on all of these.

---

## 4. How it works (5 steps)

1. **Read the code as a tree, not text** (tree-sitter parser).
   → Spaces, comments and formatting stop mattering.
2. **Erase the disguise:**
   - names → `ID`, numbers → `LIT`
   - loops *and* recursion → `LOOP`
   → Renamed code becomes **identical**.
3. **Cut each file into small pieces** (6 words each).
   → Reordering doesn't help, because we only check *which* pieces exist.
4. **Rare pieces count more.**
   → Honest students who solved the same problem don't get flagged.
5. **Score and rank every pair.** Highest first.

**No AI is used for detection.** That makes it free, fast, and the same answer every run.

---

## 5. How a pair is judged (in depth, still simple)

### 5a. The pieces

After step 2, a file is a long list of words like `def ID ( ID ) : ID = LIT LOOP ...`. We slide a window of **6 words** along it, and each window is one **piece**:

```
def ID ( ID ) :    ← piece 1
ID ( ID ) : ID     ← piece 2
( ID ) : ID =      ← piece 3
...
```

**Why 6?**
- **Too small (2–3):** every file shares pieces like `ID = LIT`, so everything looks copied.
- **Too big (10+):** one small edit breaks the piece, so copies slip through.
- **6** sits in the middle, and beat 5 on the separation margin in our tests for all 3 languages.

### 5b. Rarity weight: not all pieces are equal

Every piece gets a weight based on **how many files contain it**:

```
weight = log(1 + total files ÷ files containing this piece)
```

With 300 files:

| Piece found in… | Weight | Meaning |
|---|---|---|
| 2 files | **5.02** | Rare, strong evidence these two are linked |
| all 300 files | **0.69** | Everyone writes it (reading input), weak evidence |

So a rare shared piece counts **about 7× more** than common code. This one idea stops honest students from being flagged.

### 5c. The score: two views averaged

For files A and B, add up the weights of the pieces they share. Then compare that to two things:

| View | Question it asks | Catches |
|---|---|---|
| **Jaccard** = shared ÷ everything in A and B together | "How much of the two files overall is the same?" | Straight copies |
| **Containment** = shared ÷ the smaller file | "Is the smaller file hidden inside the bigger one?" | A copy **padded with extra junk code** |

**Final score = the average of the two.**

Example: a student copies a 50-line solution and adds 150 lines of junk.
- Jaccard alone: about **0.25** (looks innocent)
- Containment alone: about **1.0** (the whole solution is inside)
- Average: about **0.6**, so it still ranks high ✅

**Safety rule:** in the containment view, the "smaller file" is never counted as less than **half the bigger file**. Without it, a 2-line file (just "read input, print sum") would look "100% contained" in every real solution.

### 5d. Only fair comparisons

- **Only the same language is compared.** Python vs Python, Java vs Java.
- **Starter code can be removed:** with `--base starter.py`, any piece found in the teacher's template is deleted before scoring.
- **Hidden characters are removed** before parsing, so an invisible character can't break the parse and hide a copy.

### 5e. Showing the evidence

A score alone doesn't convince anyone, so the app explains each pair:

| Evidence | How it's found | Shows |
|---|---|---|
| **Matching blocks** | Shared pieces mapped back to line numbers, then joined into blocks | Highlighted lines side by side |
| **Renamed variables** | Lines up the matched code and spots names in the same role (seen 2+ times) | `distance` → `dist` |
| **Identical rare lines** | Lines exactly the same in both, skipping short or boilerplate lines (`import`, `return`, lines in 3+ files) | The exact line pairs |
| **Coverage** | % of each file's non-blank lines inside matching blocks | "72% of file A matches" |
| **Rank in batch** | Share of all pairs that score lower | "Higher than 97% of pairs" |

---

## 6. How we prove it works (our evaluation)

Five test suites run **automatically on every change** (GitHub Actions). A change can't merge if any fails.

| Test | What it checks | Pass rule |
|---|---|---|
| `test_engine` | Each disguise on its own: rename, reorder, loop→recursion, AI-style rewrite, in 3 languages | Each copy scores high, and above an **honest solution to the same task** |
| `test_problems` | 2 problems × 3 languages, scanned together: originals, AI rewrites, honest solutions | **Every** AI rewrite must outrank **every** non-copy pair |
| `test_edge_cases` | Weird input: empty, broken or huge files, wrong text encoding, Mac zip junk, hidden characters, starter code | Never crashes, never fake-flags |
| `bench` | 300 files, worst case, 12 of them watermarked | Under 2 minutes (we take about 1 s); exactly the 12 watermarked files flagged |
| `test_watermark` | Each watermark kind, look-alikes that must not flag, the demo set | Every kind found, no false flags, demo marks exactly its 2 planted files |
| `test_app` | The web app: demo set, ranking, highlighting, safe display of uploaded code | Top 6 = real copies; uploaded code can't inject HTML |

**Results:**

| Claim | Number |
|---|---|
| Speed | **300 files in about 1 second** |
| Ranking | **All 6 AI-rewritten copies rank #1–6**, above every honest pair |
| Copy vs honest (Java) | AI rewrite **0.56** vs honest solution **0.22** |
| Starter-code skip | Honest pair **0.49 → 0.01** |
| Hidden character | A copy's score dropped to 0.89 → fixed back to **1.0** |

---

## 7. Features (what to demo)

**Web app:**
- 📦 **Upload a zip** of submissions (and optional starter code)
- ▶️ **"Try the demo set"**: works without your own files
- 📊 **Ranked table** of pairs to review
- 🔍 **Side-by-side view** with matching lines highlighted
- 💡 **"Why this pair?"** evidence (section 5e)

**Protections:**
- 👻 **Hidden-character check:** flags invisible characters, often left when code is pasted from a chat window, and removes them so they can't hide a copy
- 📄 **Starter-code skip:** the teacher's template doesn't count as copying

**Demo in 2 minutes:**
1. Open the app → **Try the demo set**. The 6 real copies are on top.
2. Click the top pair: the matched logic is highlighted, despite the renames.
3. Point at "Why this pair?" and the renamed variables it found.
4. Name one honest limit (section 9).

---

## 8. How we compare to existing tools

- Universities use **MOSS, JPlag and Dolos**. Same core idea: compare structure.
- **What we add for AI rewrites:**
  - loop ↔ recursion caught
  - style-only rewrites normalized
  - hidden characters flagged and removed
  - plain "why this pair" explanations
- Full table: README → "How Dejavu compares to existing tools".

---

## 9. Honest limits (say these before they ask)

- ❌ **Copying across languages** (Python → Java) isn't caught. This is our "next step".
- ❌ **A full algorithm change** isn't caught. If the logic is different, it's arguably not a copy anymore.
- ⚠️ **A score means "check this first", not "proven cheating".** A human decides.
- ⚠️ **The test set is small and hand-made.** Thresholds may need tuning on real data.

---

## 10. Likely questions

| They ask | You say |
|---|---|
| "Why not just use ChatGPT?" | 45,000 pairs means slow, costly, and a different answer each run. Ours is free, ~1 s, and repeatable. |
| "Two honest students write the same code. False positive?" | Rarity weighting: common code counts almost nothing (0.69 vs 5.02). In our tests, honest pairs rank below every copy. |
| "Can you detect AI-written code?" | Not by style alone, and we don't claim to. We flag the **watermarks a chat tool leaves in the file**: "Generated by ChatGPT" lines, `<\|endoftext\|>` tokens, pasted markdown fences, and invisible hidden text, which we decode. Statistical watermarks need the AI company's secret key. Every flag is a *hint*, never part of the score. |
| "Why 6-word pieces?" | Smaller matches everything, bigger breaks on small edits (section 5a). |
| "What would you do with more time?" | Cross-language copies, and testing on a real labelled dataset. |
| "How did you work as a team?" | Issue → kanban board → branch per feature → pull request → 5 automated test suites must pass before merge. |
