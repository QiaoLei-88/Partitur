# Local requests

This directory is the request record for {{PROJECT}}'s code repositories. It
lives in the records repository `{{RECORDS}}/`, not in the code
repositories. Each request names its repository in the `repo` field of its
first message; the repositories, their primary checkouts (relative to the
workspace root), and main branches are listed in `repos`, one per line,
fields separated by whitespace (no field may contain any). Add a repository
by adding a line.

```
pr/
  repos     the repository table
  open/     requests waiting for review, decision, or changes
  merged/   requests merged into their repository's main branch
  closed/   requests rejected or withdrawn
```

Each request is a directory `NNNNNN-short-name` holding its conversation as
numbered message files, one file per message:

```
000001-docs-terminology/
  0001-request.md   requester: summary, authorization, branch, head, checks
  0002-review.md    integrator: analysis, comments C1, C2, ..., recommendation
  0003-decision.md  user's decision, recorded by the integrator
  0004-reply.md     requester: answers by comment ID, new head if code changed
  0005-review.md    integrator: follow-up comments and recommendation
  0006-decision.md  user's decision, recorded before the merge
  0007-cleanup.md   integrator: branches, worktrees, tags removed later
```

A review never changes a code repository and only recommends. Merging,
requesting changes, rejecting, and withdrawing follow the user's decision,
which is recorded as its own message before anything is merged or moved.
Test runs made for a review are kept under `test-runs/` in the workspace
root and cited by id (see `bin/test-run`).

Rules:

- A message file is written once by one session and never edited. The one
  standing exception: a session that finds its new message's number taken
  renames its own file to the next free number in a new commit.
- Each file starts with a front-matter header naming its kind, author role,
  session (the holder name from `/ptt-take`), date, and the head commit it
  refers to; a request also names the task it serves.
- Reviewer comments carry IDs (`C1`, `C2`, ...) continued across rounds,
  each marked required or optional; replies answer every ID.
- A request changes state only when the integrator, after the user's
  decision, moves its directory between `open/`, `merged/`, and `closed/`.
  Numbers are never reused.
- Status records (a task's `status.md`) never copy a request's state;
  `bin/pr list` gives it.

The read-only helper `bin/pr` lists requests and prints conversations:

```bash
bin/pr list                 # open requests and whose turn it is
bin/pr list all --branch docs/terminology
bin/pr show 1               # whole conversation of 000001, in order
bin/pr path 1               # directory of 000001, wherever it is
bin/pr gc                   # removable branches, worktrees, recovery tags
```

Without the helper, `tail -n +1 pr/*/000001-*/[0-9][0-9][0-9][0-9]-*.md`
prints the same conversation. Development worktrees of the code
repositories live under `worktrees/` in the workspace root.

Branches, worktrees, and `recovery/` tags of decided requests are removed
after a cooldown (default 14 days) with the `ptt-pr-cleanup` skill;
rejected and withdrawn heads are kept as `archive/pr-NNNNNN` tags.

The procedures are the `ptt-pr-submit`, `ptt-pr-draft-reply`,
`ptt-pr-reply`, `ptt-pr-review`, and `ptt-pr-cleanup` skills.
