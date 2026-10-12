---
name: ptt-pr-submit
description: Submit a local pull request for a development branch, reply to its review, or list this branch's requests, using numbered message files under <records>/pr/open/NNNNNN-name/. Arguments: list [BRANCH], reply N, or none to submit the current branch. Use when a development session has finished branch commits and wants them reviewed and integrated into its main branch, or must answer review comments.
---

# Submit or reply to a local pull request

The user's command (`/ptt-pr-submit`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

Local requests are directories under `<records>/pr/`, where `<records>`
is the project's records repository. Read `<records>/pr/README.md` for the
layout and rules; the table of repositories (`repo` values, primary
checkouts, and main branches) is `<records>/pr/repos`. Below, `<repo>` is the
request's repository (in commands and paths, its primary checkout from the
table) and `<main>` its main branch. The workspace root is the
directory that contains `<records>/`, the primary checkouts, and
`worktrees/`; confirm these locations before writing. `<records>/` is its
own Git repository.

Every write to the records repository is committed with
`<records>/bin/ptt record -m "<message>" <paths>`, never with plain Git: it
commits exactly those paths under the lock all sessions share.

The requesting session writes only its own message files. Never edit an
existing message, and never move a request directory; moving belongs to the
integrator.

## Arguments

| Argument | Action | Writes |
| --- | --- | --- |
| `list [BRANCH]` | Run `<records>/bin/pr list all --branch BRANCH` (default: the current branch) and report each request's status; "waiting for author" means the user decided to request changes and a reply is needed. | no |
| `reply N` | Reply to the review of request N (`<records>/bin/pr show N` first). | yes |
| none | Submit the current branch as a new request. | yes |

Request numbers may be given short (`4`, `pr-4`, `000004`). Listing needs no
authorization; submitting and replying are writes and need it.

## New request

1. In the development worktree, confirm the branch is committed and clean
   (`git status --porcelain` empty) and that `git diff --check <base> HEAD` is
   clean. Make the history atomic before submitting: fold fixups into the
   commits they fix, and remove WIP and reverted changes
   (`git log --stat <base>..HEAD`).
2. Record `base` as `git rev-parse <main>` and `head` as
   `git rev-parse HEAD`, both full SHAs. Check
   `git merge-base --is-ancestor <main> HEAD`; if it fails, bring the branch
   up to date with `<main>` first.
3. Allocate the request number: one more than the highest six-digit `NNNNNN`
   found in `pr/open`, `pr/merged`, and `pr/closed`. Create the directory with
   `mkdir` (without `-p`); if it already exists, another session took the
   number, so allocate again.
4. Write `0001-request.md` from the template below.
5. Record it:

   ```
   <records>/bin/ptt record -m "pr NNNNNN: submit <title>" <records>/pr/open/NNNNNN-name
   ```

   Report the request number to the user, and any `note:` the tool
   printed: if no session holds the integrator role, the request waits
   until the user opens one (`/ptt-take integrator`, in a fresh session).

## Replying to a review

Reply whenever the branch changes or a review needs an answer, without
waiting for a decision. A reply pins the new head and returns the request to
"waiting for review". Decisions only gate merging and closing.

1. If code changes are needed, commit them on the same branch and repeat the
   checks of steps 1–2 above for the new head. Rebasing and fixup/autosquash
   are normal on the request's branch. Before any rewrite, tag the old
   head as `recovery/<reason>/<branch slug>` (branch slug: the branch name
   with `/` replaced by `-`, e.g. `recovery/pre-rebase/docs-design`; add
   `-2`, `-3` when the tag exists) so that `ptt-pr-cleanup` can remove it
   after the decision. If its history was rewritten, give the
   new `base` if it changed, map old to new SHAs, and summarize
   `git range-diff <base>..<old head> <base>..<new head>`.
2. Allocate the message number: one more than the highest four-digit `MMMM`
   in the request directory. Write `MMMM-reply.md` from the template. Answer
   every comment by its ID (`C1: fixed in <sha>`, `C2: disagree, because ...`).
3. After writing, list `MMMM-*` again. If another file now has the same
   number, the reviewer wrote concurrently: rename your own file to the next
   free number before committing.
4. Record only your new file:
   `<records>/bin/ptt record -m "pr NNNNNN: reply MMMM" <file>`.

## After the decision

When the request is merged, rejected, or withdrawn, update your status
record with the outcome and, for a merge, the main-branch merge commit:
your task's `status.md` (for the designer, of `T0000`). Never record a review state there; `pr list` gives it.

## Templates

`0001-request.md`:

```markdown
---
request: NNNNNN
message: 0001
kind: request
author: requester
session: <your holder name from /ptt-take>
date: <YYYY-MM-DD>
title: <one line>
task: <the task ID this request serves (T0007), or none>
repo: <a name from pr/repos>
branch: <branch>
base: <full SHA of the main branch at submission>
head: <full SHA of the branch tip under review>
worktree: <path relative to the workspace root>
---

# <title>

## Summary
What the change does and why, and the authorization it was made under (for
example "AtE, 2026-10-11"). Distinguish agreed decisions, proposals, and
unverified assumptions.

## Commits
`git log --oneline <base>..<head>` output.

## Verification
Commands, environment, inputs, exit status, and passed/failed/skipped
counts. State what was not run.

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
session: <your holder name from /ptt-take>
date: <YYYY-MM-DD>
base: <full SHA; only when the base changed, e.g. after rebasing or rewriting>
head: <full SHA of the branch tip now under review>
---

# Reply

C1: <answer>
C2: <answer>

## New commits
`git log --oneline <previous head>..<head>`, or "none".

## Verification
What was re-run for the new head, with results.
```
