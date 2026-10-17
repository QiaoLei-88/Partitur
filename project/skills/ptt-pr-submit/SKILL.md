---
name: ptt-pr-submit
description: Submit a branch (the one named, or this task's worktree) as a local pull request for review and integration, reply to its review (reply [N]), draft either for the user to check first (draft, draft reply [N]), or list this branch's requests (list [BRANCH]). Use when branch work is ready for review or a review needs an answer.
---

# Submit or reply to a local request

The command, or an AtE naming these records, approves the records this skill
writes; other work, such as changing the branch, needs AtE (rules file) or a
draft the user approves (below).
`<records>/pr/repos` maps a `repo` name to its primary checkout and main
branch `<main>`. Request numbers may be short (`4`, `pr-4`, `000004`) and
are never reused.

The branch is the one the user names; otherwise the branch of the worktree
this holder's task works in (`worktrees/<topic>`; if several, list them and
ask). Run every git command from the workspace root with `git -C
<worktree>`; never ask the user to change directory. Without N, the request
is this branch's one open request
waiting for its author; if there is none or several, list them and ask.
With N, the request must be in `pr/open`: if `<records>/bin/pr list all`
shows it merged or closed, report its state and decision and stop. A
decided request takes no draft and no reply, and a pending draft of it
lapses; a follow-up is a new request. You write only your own new message
files: never edit a message or move a request.

| Argument | Action |
| --- | --- |
| `list [BRANCH]` | `<records>/bin/pr list all --branch BRANCH` (default: the branch above): report each status; "waiting for author" means a reply is due. |
| `draft reply [N]` | Read `<records>/bin/pr show N` and the code; show the planned change per comment (a diff where short) and the full reply text. Writes nothing. |
| `reply [N]` | Read `<records>/bin/pr show N`, then reply (below). |
| `draft` | Check the branch (Submit, steps 1-2) and show the full request text. Writes nothing. |
| none | Submit the branch (below). |

A draft is for the user to check: it writes no file and makes no commit,
and planned code changes are described, not committed. After a draft in
this conversation, the user's `reply [N]` or submit command, or an AtE
naming it, approves exactly the drafted plan with the user's changes: its
commits, their tests, and recording the message. If carrying it out needs
more than the plan, stop and ask.

`reply [N]` with no draft of it in this conversation (also after `/clear`)
does nothing yet; ask:

```
No draft for request NNNNNN in this conversation. Decide:
1. Draft first (recommended): show the code plan and reply text; nothing written
2. Do the whole chain: change the code per the comments, commit, record the reply
3. No decision, discuss further
```

## Submit

1. In the worktree (`git -C <worktree>`): the branch is committed and clean (`git status
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
