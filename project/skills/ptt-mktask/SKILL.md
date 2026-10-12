---
name: ptt-mktask
description: As a Partitur designer, draft a formal task from the recent discussion, or release a draft so that it can be taken. Arguments: none (draft a new task), release N|name, amend N. Use when the user and the designer have agreed on a piece of work and want it written down as a task, or a draft is ready to be taken.
---

# Make a task

The user's command (`/ptt-mktask`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

Only a designer makes tasks: the root designer makes top-level tasks; the
holder of a `design` task makes the subtasks of its scope. `<name>` is this
session's holder name.

## Draft (no argument)

1. From the recent discussion, decide with the user: a short slug
   (`wall-distance`), the kind (`track` for research, `worker` for
   implementation, `design` for a sub-scope with its own tasks), and the
   tasks it depends on, if any.
2. Run

   ```
   <records>/bin/ptt mktask <slug> --as <name> --kind <kind> [--depends N,N]
   ```

   It prints the new charter's path.
3. Fill in the charter from the discussion: goal, read-first list (by
   repository, path, and commit or request number), scope, where results
   go, out of scope, acceptance criteria checkable from records. Mark what
   the user agreed and what is your proposal.
4. Show the charter to the user. It stays a draft, editable, until
   released; record the edits with
   `<records>/bin/ptt record -m "task <N>: charter draft" <charter path>`.

## Release (`release N`)

When the user runs `/ptt-mktask release N` (or `release <name>`) for a
complete draft:
`<records>/bin/ptt ready <N> --as <name>`. The charter is committed as
released and frozen; the task can now be taken (`/ptt-take <N>`).

## Amend (`amend N`)

A released charter is never edited. A change the user agrees to is an
amendment: `<records>/bin/ptt amend <N> --as <name> --text "<change>"`,
with `--depends N,N` to replace the task's dependencies (checked for
cycles). Tell the user to notify the holder, if any.
