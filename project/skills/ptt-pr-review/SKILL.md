---
name: ptt-pr-review
description: List, show, and review local requests in <records>/pr as the integration session. A review never changes the code repository; it writes a review message with analysis, comments, and a recommendation, then waits for the user's decision, which alone triggers a merge, a change request, or a rejection. Arguments: list [open|merged|closed|all], show N, N (review one request), all. Use when asked to list, show, review, integrate, or merge pending requests.
---

# Review local pull requests

The user's command (`/ptt-pr-review`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

Local requests are directories under `<records>/pr/`, where `<records>`
is the project's records repository. Read `<records>/pr/README.md` for the
layout and rules; the table of repositories (`repo` values, primary
checkouts, and main branches) is `<records>/pr/repos`. Below, `<repo>` is the
request's repository (in commands and paths, its primary checkout from the
table) from its first message and `<main>` its main branch. The
workspace root is the directory that contains `<records>/`, the primary
checkouts, `worktrees/`, and `test-runs/`; confirm these locations before
acting. `<records>/` is its own Git repository.

Every write to the records repository is committed with
`<records>/bin/ptt record -m "<message>" <paths>`, never with plain Git: it
commits exactly those paths under the lock all sessions share.

Listing and showing need no role. Reviewing and everything after it are
the integrator's: this session must hold the integrator role, and its
holder name (`integrator-N`) is its `session:` in every message. If it
holds none, run `<records>/bin/ptt who`: if the role is free, ask the user
to run `/ptt-take integrator` in this session (or, better, in a fresh one)
and stop; if another session holds it, tell the user and stop.

The read-only helper `<records>/bin/pr` lists and shows requests. Request
numbers may be given short: `4`, `0004`, `pr-4`, and `000004` are the same
request.

## Arguments

| Argument | Action |
| --- | --- |
| none, or `list [open\|merged\|closed\|all]` | Run `<records>/bin/pr list ...` and report the table, including each open request's status, and its cleanup line if printed. |
| `show N` | Run `<records>/bin/pr show N` and report the conversation. |
| `N` | Review request N with the procedure below, then wait for the user's decision. |
| `all` | Review every open request whose status is "waiting for review", lowest number first, then wait for a decision on each. |

## What a review may and may not change

- A review is read-only for the code repository: no merge, commit, checkout,
  or branch change in `<repo>/` or any worktree.
- It may write its own review message in the request directory, and test-run
  records under `test-runs/` created with `<records>/bin/test-run new`.
- Merging into `<main>`, moving a request directory, and closing a request
  happen only after the user's explicit decision with AtE (step 7).
- Never edit an existing message. Do not delete branches, worktrees, or
  tags; after a decision they are removed later with the `ptt-pr-cleanup` skill.

## Reviewing one request

At the start of an integration session, read
`<records>/handoff/integrator.md` first: open concerns and pending
housekeeping left by earlier sessions.

1. Read the whole conversation in order: `<records>/bin/pr show N`. Review
   only if `<records>/bin/pr list` shows "waiting for review"; otherwise
   report the status and stop.
2. Take `head`, and `base`, from the latest requester message that gives
   each (request or reply). Check that `git -C <repo> rev-parse <branch>`
   equals `head`. If not, the request is stale: say so in the review instead
   of reviewing a moving branch.
3. Check the base: `git -C <repo> merge-base --is-ancestor <main> <head>`.
   If it fails, recommend bringing the branch up to date with `<main>`.
4. Review the change: on the first round `<base>..<head>`, later rounds the
   new commits since the previously reviewed head, plus the answers to earlier
   comments. Check each commit's diff, `git diff --check`, and consistency
   with the project instructions and design documents. Check the history
   too, with `git log --stat <base>..<head>`:
   - Each commit addresses one logical problem, with its related tests and
     documentation, and its message describes what it actually changes.
   - Messy history: fixup or WIP commits, a change followed by its revert or
     rework, commits that mix unrelated changes, one change split across
     commits, merges of `<main>` into the branch, or a commit that clearly
     cannot build or pass its tests on its own.

   Messy history gets a comment asking for cleanup by rebase and
   fixup/autosquash (routine on an unmerged branch), naming the commits and
   the intended result. A required cleanup comment means recommending
   changes-requested. Do not ask to squash meaningful separate commits into
   one; the aim is atomic commits, not fewer commits.
5. Re-run verification when the change or its risk warrants it. For each run,
   create a record with `<records>/bin/test-run new <checkout at head>`, put
   commands, environment, logs, outputs, exit status, and
   passed/failed/skipped counts in that directory, and cite its id in the
   comments. Build and run in a location that does not modify the reviewed
   checkout, such as a build directory inside the run record.
6. Write `MMMM-review.md` from the template: allocate one more than the
   highest `MMMM` in the directory, and number comments continuing from
   earlier rounds (`C4`, `C5`, ...). After writing, list `MMMM-*` again; if
   another file has the same number, the later writer renumbers: if the other
   file is already recorded, rename yours to the next free number. Record only
   this file: `<records>/bin/ptt record -m "pr NNNNNN: review MMMM" <file>`.
   Report the analysis, comments, and recommendation to the user, end with
   the decision as a numbered list (the rules file's form), your
   recommendation first, and stop:

   ```
   Decide request NNNNNN:
   1. Request changes (recommended): C1, C2
   2. Merge anyway
   3. Reject
   4. No decision, discuss further
   ```
7. When the user decides with AtE, an option number with `AtE` (merge, request changes, reject, or
   withdraw, possibly with modified comments), write `MMMM-decision.md` from
   the template, recording the user's decision and any changed comments, and
   record it before anything else:

   ```
   <records>/bin/ptt record -m "pr NNNNNN: decision <merge|changes requested|reject|withdraw>" <file>
   ```
   Then:
   - **Merge**: check again that the main branch is an ancestor of the
     head (`git -C <repo> merge-base --is-ancestor <main> <head>`); it may
     have moved since the review. If not, record that the requester must
     bring the branch up to date, and stop. Otherwise, in the primary
     checkout of `<repo>` on `<main>`, with a clean worktree, run
     `git merge --no-ff <head> -m "Merge <branch> (pr NNNNNN)"`. The message
     is how the merge commit is found later, so keep it exact. Then move
     and record the request in one step:

     ```
     <records>/bin/ptt pr-move NNNNNN merged -m "pr NNNNNN: merged as <merge commit SHA>"
     ```
   - **Request changes**: leave the request in `open/`; the author replies.
   - **Reject** or **withdraw**:

     ```
     <records>/bin/ptt pr-move NNNNNN closed -m "pr NNNNNN: <rejected|withdrawn>"
     ```
8. Before the session ends, or when the user asks: put any open concern or
   pending housekeeping into `<records>/handoff/integrator.md` and record it
   (`<records>/bin/ptt record`). After a decision is recorded, or when nothing
   waits for review, and after substantial work since the last clear, offer
   once to be cleared (`/clear`) if all three hold: nothing uncommitted, open
   concerns in `integrator.md`, nothing agreed with the user only in
   conversation. State the three checks in the offer.

## Templates

`MMMM-review.md`:

```markdown
---
request: NNNNNN
message: MMMM
kind: review
author: integrator
session: <your holder name from /ptt-take>
date: <YYYY-MM-DD>
head: <full SHA reviewed>
recommendation: <merge|changes-requested|reject>
test_runs: <run ids, or none>
---

# Review

## Analysis
What changed, risks, what was checked and what was not.

## Checks
Commands run and their results; test-run ids.

## Comments
C1 (required): <comment>
C2 (optional): <comment>

## Recommendation
<merge|request changes|reject>, with reason. Waiting for the user's decision.
```

`MMMM-decision.md`:

```markdown
---
request: NNNNNN
message: MMMM
kind: decision
author: user
recorded_by: <your holder name from /ptt-take>
date: <YYYY-MM-DD>
head: <full SHA decided on>
decision: <merge|changes-requested|reject|withdraw>
---

# Decision

<The user's decision as stated, and any comments added, removed, or changed
relative to the review.>
```
