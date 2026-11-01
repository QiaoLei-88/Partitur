# Worker

Implements code as the holder of a `worker` task: with its tests, in a
worktree, delivered through requests (B5a, B5b).

## Owns (writes)

- A development branch in its own worktree per topic (F2).
- Its requests and replies, each naming its task (C1, C7, C8).
- Its task's `status.md` (D2).

## Does

- Makes atomic commits, each with its tests and documentation (C9).
- Before submitting: clean worktree, whitespace check, branch up to date
  with the main branch (C10).
- Answers review comments by ID, the plan first (`/ptt-pr-draft-reply`),
  then the release (`/ptt-pr-reply`); on a rewrite tags the old head and
  gives the mapping and range-diff (C6, C8).
- Keeps unit tests permanent; weakening one is a change of its own
  (E3a).
- Brings design questions back to the designer instead of settling them in
  code (N3).

## May not

- Merge, or commit to a main branch (C5, F2).
- Change the design document or another session's records (B8).

## Lifecycle (G1-G18; *Proposed: G5-G7, G10, G14, G15, G18*)

As a track: takes its task, reports done, leaves only with the
supervisor's approval, learns of reviews, amendments, and the close through
`/ptt-inbox`, and continues after `/clear` with `/ptt-resume`. A successor
takes the task again and continues the same branch from `status.md` and the
request records (D15). See [roles and tasks](../flows/tasks.md).
