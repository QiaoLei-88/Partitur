---
name: ptt-pr-cleanup
description: As the integrator, remove the worktrees, branches, and recovery tags of decided requests after a cooldown (default 14 days); reports the plan, runs it only on AtE. Use to clean up, prune, or gc decided requests. Argument: none or --days N.
---

# Clean up decided requests

The command, or an AtE naming these records, approves the records this skill
writes; running the removal needs AtE (rules file). Cleanup belongs to the
integrator.

## What is removed

Requests in `pr/merged/` or `pr/closed/` decided at least N days ago
(default 14; merged: from the merge commit, rejected: from the decision's
`date`):

- **Merged**: the worktree (`git worktree remove`) and the branch
  (`git branch -d`); the merge keeps the head reachable.
- **Rejected**: the worktree, a tag `archive/pr-NNNNNN` on the decided head
  (the rejected work stays reachable), then `git branch -D`.
- **Recovery tags** `recovery/<reason>/<branch with / as ->` of those
  branches: superseded drafts.

`<records>/bin/pr gc` skips, with the reason, a branch whose tip moved after
the decision, whose worktree has changes or untracked or ignored files, that
is checked out in the primary checkout, whose merged head is not in the main
branch, or whose `archive/` tag points elsewhere, and every branch of a
repository whose primary checkout is not on its main branch. A branch name
used by several requests goes only when none is open, waiting, or skipped;
its recovery tags likewise. Never touched: branches without a request, open
requests, `test-runs/`, `archive/` tags, main branches and their tags. Never
use `--force`; never edit a message.

## Procedure

1. `<records>/bin/pr gc [--days N]` (read-only): report its table and
   commands, end with `1. Run all listed commands`, `2. Run them only for
   the requests or tags I name`, `3. No decision, discuss further`, and
   stop.
2. On AtE (possibly limited to some requests or tags): run `pr gc` again
   with the same `--days`; if the plan changed for the approved items,
   report and stop.
3. Run the approved commands in order, one request at a time. If one fails,
   skip that request's remaining commands, report, and go on only with
   independent requests. Finish with the listed `git worktree prune`.
4. For each request with something removed, write `MMMM-cleanup.md` (one
   more than the highest `MMMM`) and record only those files:
   `<records>/bin/ptt record -m "pr NNNNNN: cleanup" <files>`.
5. Run `pr gc` again and report what remains. In
   `<records>/handoff/integrator.md`, "Pending housekeeping": drop what was
   done, list what waits with its due date; record it.

## Template

`MMMM-cleanup.md`:

```markdown
---
request: NNNNNN
message: MMMM
kind: cleanup
author: integrator
session: <holder name>
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
