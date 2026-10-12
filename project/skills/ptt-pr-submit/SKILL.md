---
name: ptt-pr-submit
description: Submit the current branch as a local pull request for review and integration, reply to its review (reply N), or list this branch's requests (list [BRANCH]). Use when branch work is ready for review or a review needs an answer.
---

# Submit or reply to a local request

The command approves only the records this skill writes; other work, such
as changing the branch, needs AtE (rules file). `<records>/pr/repos` maps a
`repo` name to its primary checkout and main branch `<main>`. Request
numbers may be short (`4`, `pr-4`, `000004`) and are never reused. You
write only your own new message files: never edit a message or move a
request.

| Argument | Action |
| --- | --- |
| `list [BRANCH]` | `<records>/bin/pr list all --branch BRANCH` (default: current branch): report each status; "waiting for author" means a reply is due. |
| `reply N` | Read `<records>/bin/pr show N`, then reply (below). |
| none | Submit the current branch (below). |

## Submit

1. In the worktree: the branch is committed and clean (`git status
   --porcelain` empty, `git diff --check <main> HEAD` clean) and its history
   atomic (`git log --stat <main>..HEAD`: fold fixups, drop WIP and
   reverted changes).
2. `base` = `git rev-parse <main>`, `head` = `git rev-parse HEAD`, full
   SHAs. If `git merge-base --is-ancestor <main> HEAD` fails, update the
   branch first.
3. Number: one more than the highest six-digit `NNNNNN` in `pr/open`,
   `pr/merged`, `pr/closed`. `mkdir <records>/pr/open/NNNNNN-<short-name>`
   (e.g. `000001-docs-terminology`) without `-p`; if it exists, allocate
   again.
4. Write `0001-request.md` from the template and record it:
   `<records>/bin/ptt record -m "pr NNNNNN: submit <title>"
   <records>/pr/open/NNNNNN-name`. Report the number and any `note:` the
   tool printed (no integrator: the request waits until the user opens one
   with `/ptt-take integrator`).

## Reply

Reply whenever the branch changes or a review needs an answer, without
waiting for a decision (decisions only gate merging and closing); a reply
pins the new head and returns the request to "waiting for review".

1. Code changes are commits on the same branch, checked as in steps 1-2.
   Before rewriting history, tag the old head `recovery/<reason>/<branch
   with / as ->` (`-2`, `-3` if taken), for `ptt-pr-cleanup` to remove
   later; after a rewrite give the new `base` if it changed, the old-to-new
   SHA map, and a `git range-diff <base>..<old head> <base>..<new head>`
   summary.
2. Write `MMMM-reply.md` (one more than the highest `MMMM`), answering every
   comment by ID (`C1: fixed in <sha>`, `C2: disagree, because ...`). List
   `MMMM-*` again; if another file has your number and is already
   recorded, rename yours to the next free one.
3. Record only it: `<records>/bin/ptt record -m "pr NNNNNN: reply MMMM" <file>`.

After the decision (merged, rejected, or withdrawn), put the outcome (and,
for a merge, the merge commit) in your task's `status.md` (the designer's:
of `T0000`), never a review state.

## Templates

`0001-request.md`:

```markdown
---
request: NNNNNN
message: 0001
kind: request
author: requester
session: <holder name>
date: <YYYY-MM-DD>
title: <one line>
task: <task ID served (T0007), or none>
repo: <name from pr/repos>
branch: <branch>
base: <full SHA of main at submission>
head: <full SHA of the branch tip>
worktree: <path relative to the workspace root>
---

# <title>

## Summary
What and why; the authorization it was made under (for example "AtE,
2026-10-11"). Distinguish agreed decisions, proposals, and unverified
assumptions.

## Commits
`git log --oneline <base>..<head>`.

## Verification
Commands, environment, inputs, exit status, passed/failed/skipped counts;
what was not run.

## Open items
Known limitations and unfinished work.
```

`MMMM-reply.md`:

```markdown
---
request: NNNNNN
message: MMMM
kind: reply
author: requester
session: <holder name>
date: <YYYY-MM-DD>
base: <full SHA; only if the base changed>
head: <full SHA of the branch tip now under review>
---

# Reply

C1: <answer>

## New commits
`git log --oneline <previous head>..<head>`, or "none".

## Verification
What was re-run for the new head, with results.
```
