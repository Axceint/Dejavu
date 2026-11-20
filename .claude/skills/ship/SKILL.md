---
name: ship
description: Verify and ship Dejavu work through issue -> branch -> PR -> review. Use when asked to commit, push, ship, open a PR, or move a board card in this repo.
---
Never push to `main`. Commits are authored by the human only (their git config); no Co-Authored-By or AI attribution lines in commits or PR bodies.

1. Work has a GitHub issue (`gh issue create -R Axceint/Dejavu -a <login> -l bug|enhancement`). Add it to the board: `gh project item-add 4 --owner itzhimanshugt --url <issue-url>`.
2. Branch from fresh main: `git switch main; git pull; git switch -c himu/<topic>` (Akshit uses `akshit/<topic>`).
3. From repo root run `.venv\Scripts\python -m tests.test_engine` and `.venv\Scripts\python -m tests.bench`. Stop and report if either fails.
4. Edit files with the Edit tool, never PowerShell Get/Set-Content (PS 5.1 corrupts UTF-8).
5. Commit `"<what> (closes #N)"`, `git push -u origin <branch>`, then `gh pr create -R Axceint/Dejavu -B main -r <other teammate>` with body: `Closes #N`, problem, change, results table, how to verify.
6. Don't merge your own PR; the other teammate reviews and merges after CI is green.

Board columns (project 4, owner itzhimanshugt). Move a card:
`gh project item-edit --project-id PVT_kwHOCpPskc4Bshr2 --id <item-id> --field-id PVTSSF_lAHOCpPskc4Bshr2zhqvdEo --single-select-option-id <opt>`
Options: Todo `f75ad846`, In Progress `47fc9ee4`, Done `98236657`. Item ids: `gh project item-list 4 --owner itzhimanshugt --format json`.
Merged PRs with `Closes #N` close the issue; set its card to Done.
