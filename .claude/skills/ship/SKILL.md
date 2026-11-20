---
name: ship
description: Verify and ship Dejavu work through issue -> branch -> PR -> CI -> merge. Use when asked to commit, push, ship, open a PR, or move a board card in this repo.
---
Never push to `main`. Commits are authored by the human only (their git config); no Co-Authored-By or AI attribution lines in commits or PR bodies.

1. Work has a GitHub issue (`gh issue create -R Axceint/Dejavu -a <login> -l bug|enhancement`). Add it to the board: `gh project item-add 4 --owner itzhimanshugt --url <issue-url>`.
2. Branch from fresh main: `git switch main; git pull; git switch -c himu/<topic>` (Akshit uses `akshit/<topic>`).
3. From repo root run every step in `.github/workflows/test.yml` (`.venv\Scripts\python -m tests.<name>`). Stop and report if any fails.
4. Edit files with the Edit tool, never PowerShell Get/Set-Content (PS 5.1 corrupts UTF-8).
5. Commit `"<what> (closes #N)"`, `git push -u origin <branch>`, then `gh pr create -R Axceint/Dejavu -B main -r <other teammate>` with body: `Closes #N`, problem, change, results table, how to verify.
6. Merge only after CI passes on the PR's *current* head commit; no self-approval or approval bots. Before merging, `gh pr update-branch <N>` so CI tests it against latest main. Wait on the exact commit (Bash), since `gh pr checks` can report the previous run:
   ```bash
   sha=$(gh pr view N -R Axceint/Dejavu --json headRefOid --jq .headRefOid)
   id=$(gh run list -R Axceint/Dejavu -b <branch> --json databaseId,headSha --jq ".[] | select(.headSha==\"$sha\") | .databaseId" | head -1)
   gh run watch "$id" -R Axceint/Dejavu --exit-status && gh pr merge N -R Axceint/Dejavu --squash --delete-branch
   ```
   If `id` is empty the run hasn't registered yet; retry the `gh run list` after a few seconds.

Board columns (project 4, owner itzhimanshugt). Move a card:
`gh project item-edit --project-id PVT_kwHOCpPskc4Bshr2 --id <item-id> --field-id PVTSSF_lAHOCpPskc4Bshr2zhqvdEo --single-select-option-id <opt>`
Options: Todo `f75ad846`, In Progress `47fc9ee4`, Done `98236657`. Item ids: `gh project item-list 4 --owner itzhimanshugt --format json`.
Merged PRs with `Closes #N` close the issue; set its card to Done.
