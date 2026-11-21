# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + TypeScript + Vite single-page app on the FastAPI layer in `dejavu/api.py` (Python 3.12). Replaces the Streamlit app (`app.py`), which retires in phase 6. Hosting target undecided: Render or Hugging Face Spaces.

## Users

Primary: a programming-contest judge, live, during or right after a contest. They have a batch of up to ~300 submissions in Python, C++ and Java and little time. Their job is to triage fast: see which pairs to check first, confirm or dismiss each with evidence, and move on.

Secondary: a teacher or TA reviewing one batch after a deadline (the same flow, done more slowly).

Evaluators: hackathon judges. They watch a live demo and also open the hosted link to try it themselves afterwards.

## Product Purpose

Dejavu finds students who copied code, even after an AI rewrote it to look different. It turns ~45,000 possible pairs into a ranked queue of pairs to check first. A human makes the final call. Success means a judge reaches the real copies early in the queue and can show why each one is a copy.

## Positioning

It compares code structure, not text: it parses with tree-sitter and erases the disguise (renames, reordering, loop to recursion, style, AI noise such as docstrings and type hints) before it compares. Rare shared structure counts more than code everyone writes. Every flagged pair comes with evidence (matching lines, renames, verbatim runs) instead of a bare score.

## Operating Context

- Upload one `.zip` of submissions. Optionally add starter code, whose matches are ignored. A built-in demo set exists.
- Progress through the stages read, parse, compare and explain, delivered by polling.
- Review a ranked pair queue: open a side-by-side comparison, decide, add notes.
- Export: a CSV of all pairs, with decisions, and an offline HTML report that opens without a server.
- Decisions are saved in the browser per batch.

## Capabilities and Constraints

Must not change:

- scan, scoring and evidence logic;
- `render()` escaping (`<` becomes `<`) and its theme whitelist;
- CSV formula escaping in both exports;
- the starter file keeps its suffix;
- limits: MATCH_TOP=100 and LIMIT=500;
- saved decisions: localStorage key `dejavu:<payload id>`, pair key `fileA\nfileB`.

The tool never decides: it ranks and shows evidence, and the judge marks.

Planned features, in this order:

1. Exact search across all files, plus a Ctrl+K command palette. No AI.
2. Disguise X-ray: both files shown as the engine's normalized tokens, lined up.
3. Similarity Atlas: a graph of pairs that highlights copy rings (3+ students sharing one source).
4. "Ask the batch": a read-only RAG panel. Backend is done. Every answer cites file:line with clickable citations. It cannot mark, sort or decide. There is one index per upload, deleted with the scan. The panel is hidden when there is no API key or no internet.
5. If time allows: Dejavu memory, i.e. fingerprints of past batches.

Undecided: whether to keep or drop the current coffee-house visual style (a team decision).

## Brand Commitments

Name: Dejavu. Voice: plain and factual. It says "pairs to check first" and never accuses: a match is evidence for a human, not a verdict.

## Evidence on Hand

- `tests/problems/`: the built-in demo set.
- `demo/`: a 300-file zip with an answer key (local, not committed).
- Live Streamlit backup: https://dejavu.streamlit.app/
- `PITCH.md` and `README.md`: the walkthrough and technical detail.
- No user testimonials, adoption numbers or accuracy claims beyond the repo's own tests and benchmark. Don't invent any.

## Product Principles

1. Speed to the first real copy: the queue order and the first screen serve a judge under time pressure.
2. Evidence over verdicts: every flag shows why, and the human decides.
3. Nothing is lost: decisions persist per batch, and exports work offline.
4. Read-only intelligence: search, X-ray, Atlas and Ask explain, and they never mark or sort.

## Accessibility & Inclusion

WCAG 2.2 AA. The whole review flow works from the keyboard (keyboard map planned for phase 4), with visible focus and screen-reader labels. Colour is never the only carrier of meaning in highlights or scores.
