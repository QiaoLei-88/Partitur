# Task {{NUMBER}}: {{TITLE}}

The designer's charter for this task. It is frozen once the task is
released; later changes are amendments (`ptt amend`). The holder writes only
`status.md` next to it. This charter authorizes nothing: writes, builds,
commits, and requests need the user's AtE as usual.

The optional front-matter `tool:` is `claude`, `codex`, or `any` (the
default when absent). Set it with `ptt mktask --tool` or in this draft;
after release, change it with `ptt amend --tool`. A restricted task can be
taken only by a session whose tool is known and matches.

## Goal

{{WHAT this task must achieve, and why, in two or three sentences}}

## Read first

- The rules file.
- {{DOCUMENTS, by repository, path, and commit or request number}}

## Scope

1. {{STEP}}

## Where results go

- {{OUTPUTS: notes, code, run records}}.
- Delivery: {{REPOSITORY from pr/repos}}, on branches in
  `worktrees/<task slug>`, through requests (`/ptt-pr-submit`, naming this
  task); run records under `test-runs/`.
- Findings that affect the design: `status.md`, or a note to the designer.

## Merge order

{{For each prerequisite: after: <task or request>; reason: <why merging
waits>; cleared when: <condition that satisfies the prerequisite>. Or:
Independent of other open tasks.}}

This order gates merging; work may start. `depends:` instead gates taking
the task until its dependencies are closed.

## Out of scope

- Design decisions without the user.
- {{EXCLUSIONS}}

## Acceptance

- {{CHECK of the goal itself, as a command where one exists, with its
  expected result; rules file, goal acceptance}}
- {{CRITERIA, checkable from records}}
- Unknowns and skipped work stated as such.
