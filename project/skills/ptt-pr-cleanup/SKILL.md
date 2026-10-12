---
name: ptt-pr-cleanup
description: Remove the worktrees, branches, and recovery tags of decided local requests after a cooldown (default 14 days), as the integration session. Without AtE it only reports the plan from `<records>/bin/pr gc`; with AtE it runs the listed commands and records a cleanup message per request. Arguments: none or `--days N`. Use when asked to clean up, prune, or garbage-collect merged or rejected request branches and worktrees.
---

# Clean up decided local pull requests

The user's command (`/ptt-pr-cleanup`) is the approval for the records this
skill writes, and for nothing else; the work itself still needs AtE. Agreement
in conversation without the command is not approval.

Local requests are directories under `<records>/pr/`, where `<records>`
is the project's records repository. Read `<records>/pr/README.md` for the
layout and rules; the table of repositories is `<records>/pr/repos`. The
workspace root is the directory that contains `<records>/`, the primary
checkouts, `worktrees/`, and `test-runs/`; confirm these locations before
acting. Cleanup belongs to the integration session.

## What is removed

For each request in `pr/merged/` or `pr/closed/` whose decision is at least
N days old (default 14): for merged requests the age is measured from the
merge commit, for rejected ones from the decision message's `date`.

- **Merged**: the branch's worktree (`git worktree remove`) and the branch
  (`git branch -d`). The merge keeps the decided head reachable from the main
  branch.
- **Rejected**: the worktree, then tag the decided head as
  `archive/pr-NNNNNN` so the rejected work stays reachable, then
  `git branch -D`.
- **Recovery tags** `recovery/<reason>/<branch slug>` (branch slug: the
  branch name with `/` replaced by `-`) of those branches. Superseded
  pre-rebase or pre-fixup heads are drafts; after the decision and cooldown
  they need not stay reachable.

A branch is skipped, with the reason shown, when its tip moved after the
decision, its worktree has any changes or untracked or ignored files, it is
checked out in the primary checkout, a merged head is not in the main branch,
the primary checkout is not on its main branch, or an `archive/` tag exists
at another commit. A branch name reused by several requests is removed only
when none of them is open, waiting, or skipped. Recovery tags of a branch
follow the same rule, and tags of a main branch are never listed.

Never touched: branches without a request (another session's work), open
requests, `test-runs/` records (reviews cite them), `archive/` tags, and the
main branches. Never use `--force` and never edit an existing message.

## Procedure

1. Run `<records>/bin/pr gc [--days N]`. It is read-only and prints a table
   (remove, wait, or skip with a reason) and the exact commands, grouped by
   request. Report the table and commands to the user, and stop. Without AtE
   nothing further happens.
2. After the user's AtE, possibly limited to some requests or tags, run
   `<records>/bin/pr gc` again with the same `--days` and check that the plan
   is unchanged for the approved items; if it changed, report and stop.
3. Run the approved commands in order, one request at a time. If a command
   fails, run none of that request's remaining commands, report the error,
   and continue with other requests only if their commands are independent.
   Finish with the listed `git worktree prune`.
4. For each request with something removed, write `MMMM-cleanup.md` (one
   more than the highest `MMMM` in its directory) from the template, then
   record only those files:

   ```
   <records>/bin/ptt record -m "pr NNNNNN: cleanup" <files>
   ```
5. Run `<records>/bin/pr gc` once more and report what remains. Update the
   "Pending housekeeping" section of `<records>/handoff/integrator.md`: drop
   what was done, and list what waits with the date it becomes due; record
   it (`<records>/bin/ptt record`).

## Template

`MMMM-cleanup.md`:

```markdown
---
request: NNNNNN
message: MMMM
kind: cleanup
author: integrator
session: <your holder name from /ptt-take>
date: <YYYY-MM-DD>
head: <full SHA of the decided head>
cooldown_days: <N>
---

# Cleanup

Commands run, each with its output, for example:

- `git worktree remove ../worktrees/name`
- `git branch -d branch` (was <sha>)
- `git tag archive/pr-NNNNNN <sha>` (rejected requests)
- `git tag -d recovery/<reason>/<slug>` (was <sha>)

Anything skipped, with the reason.
```
