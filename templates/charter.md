# Task {{NUMBER}}: {{TITLE}}

The designer's charter for this task. It is frozen once the task is
released; later changes are amendments (`ptt amend`). The holder writes only
`status.md` next to it. This charter authorizes nothing: writes, builds,
commits, and requests need the user's AtE as usual.

## Goal

{{WHAT this task must achieve, and why, in two or three sentences}}

## Read first

- The rules file.
- {{DOCUMENTS, by repository, path, and commit or request number}}

## Scope

1. {{STEP}}

## Where results go

- {{OUTPUTS: notes, code, run records}}.
- Delivery: {{REPOSITORY from pr/repos}}, on branches in `worktrees/<topic>`,
  through requests (`/ptt-pr-submit`, naming this task); run records under
  `test-runs/`.
- Findings that affect the design: `status.md`, or a note to the designer.

## Out of scope

- Design decisions without the user.
- {{EXCLUSIONS}}

## Acceptance

- {{CRITERIA, checkable from records}}
- Unknowns and skipped work stated as such.
