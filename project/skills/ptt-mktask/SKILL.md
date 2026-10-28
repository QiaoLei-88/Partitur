---
name: ptt-mktask
description: "As a designer, draft a task from the agreed discussion, release a draft for taking, or amend a released charter. Arguments: none (draft), release N|name, amend N."
---

# Make a task

The command, or an AtE naming these records, approves the records this skill
writes; other work needs AtE (rules file). Only a designer makes tasks: the
holder of `T0000` the top-level tasks, the holder of a `design` task the
subtasks of its scope. `<name>` is your holder name.

## Draft (no argument)

1. From the recent discussion, decide with the user: a slug
   (`wall-distance`), the kind (`track` research, `worker` implementation,
   `design` a sub-scope with its own tasks), and the tasks it depends on, if
   any.
2. `<records>/bin/ptt mktask <slug> --as <name> --kind <kind> [--depends N,N]`
   prints the charter's path.
3. Fill in the charter from the discussion (or a brief the user names, cited
   as its source): goal, read-first list by repository, path, and commit or
   request number, scope, where results go, out of scope, acceptance
   criteria checkable from records. Mark what the user agreed and what you
   propose.
4. Show it to the user. A draft stays editable until released; record edits
   with `<records>/bin/ptt record -m "task <N>: charter draft" <charter>`.

## Release (`release N`)

For a complete draft: `<records>/bin/ptt ready <N> --as <name>`: the charter
is committed and frozen; the task can be taken (`/ptt-take <N>`).

## Amend (`amend N`)

A released charter is never edited; an agreed change is an amendment:
`<records>/bin/ptt amend <N> --as <name> --text "<change>"`, with `--depends
N,N` to replace its dependencies (checked for cycles). A holder sees it in
its inbox (in Claude Code with the user's next message to it, otherwise at
its next `/ptt-inbox`).
