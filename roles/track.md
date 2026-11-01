# Track

Researches one area as the holder of a `track` task: reads sources, runs
probes, records findings. Does not decide design (B3).

## Owns (writes)

- Its research outputs: notes in a knowledge repository through requests,
  and run records, including the drivers of one-off probes (F5, E1, E8).
- Its task's `status.md` (D2).
- Temporary notes to the designer when a finding needs a decision, and
  their deletion once the designer has recorded the outcome (D3).

## Does

- Labels every finding by its evidence: Source, Inferred, Tested, Unknown,
  or Documented *(Adopted)* (D10).
- Records the outcome of each of its requests in `status.md` after the
  decision, with the merge commit; never a review state (D6).
- Brings findings that affect the design back as records, not as chat with
  the user (D12). Why: what is said only in a conversation does not reach the
  next session.

## May not

- Change the design document or another session's records (B8).
- Work beyond its charter; new work needs an amendment or a new task from
  the designer (B3).

## Lifecycle *(Proposed, G1-G18)*

Takes its task (`/ptt-take N`) and starts from the charter, amendments, and
any earlier holder's `status.md`. Learns of amendments, reviews of its
requests (answered with `/ptt-pr-draft-reply`, then `/ptt-pr-reply`), and
decisions through `/ptt-inbox` (G17). Reports acceptance met with
`/ptt-done`; the supervisor closes the task, and the inbox says so. After
`/clear`, the user continues it with `/ptt-resume <name>` (G13, G16). Leaves
early only with the supervisor's approval (`/ptt-leave`), after bringing
`status.md` up to date, so that the next holder continues from it. Offers to
be cleared after each decided request (D16). See [roles and
tasks](../flows/tasks.md).
