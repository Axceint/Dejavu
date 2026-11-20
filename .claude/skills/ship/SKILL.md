---
name: ship
description: Verify and push Dejavu work to GitHub as the human author. Use when asked to commit, push, ship, or save progress in this repo.
---
1. From repo root run `.venv\Scripts\python -m tests.test_engine` and `.venv\Scripts\python -m tests.bench`. Stop and report if either fails.
2. Update the Status checklist in `STATUS.md` if a task finished.
3. `git add -A`, then commit with a one-line message. No Co-Authored-By or AI attribution lines: commits are authored by the human (their own git config).
4. `git push` to the current branch (`main` until branches `himu/*`/`akshit/*` exist).
5. Reply with the commit hash and one line of what changed.
