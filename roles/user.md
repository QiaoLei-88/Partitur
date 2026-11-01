# User (authority)

The one human in the project. Partitur exists so that the user can direct
many sessions without holding their details.

## Decides

- What is done: every task starts with the user's AtE, or AtEiYA when the
  session agrees (A2, A3). The user may give one session a standing
  authorization for a scope *(Adopted, A8)*.
- What enters a main branch: merge, change request, or rejection of every
  request, recorded by the integrator as a decision message (B1, C5, C16);
  withdrawal of a request *(Proposed, C19)*.
- Every design decision labelled Agreed, with the designer of its scope
  (B2, D10).
- Whether to open or resume a session *(Adopted, B10)*, and which role or
  task it takes (`/ptt-take`) *(Proposed, G1)*.
- The root designer's charter, `T0000` (amendments with `--as user`), when
  a designer or integrator leaves, and freeing one whose holder is gone
  (`/ptt-leave free designer`) *(Proposed, G4, G7)*.

## Does

- Approves records by running the `/ptt-*` command, or by an AtE naming
  them, and decides by option number (`1 AtE`) *(Proposed, A12, A13)*.
- Carries notices between sessions only where no prompt hook delivers
  them; the substance is in records (D12, G17).
- Supplies inputs only the user has: data, cases, baselines, priorities.

## Need not do

- Read every record. Reviews, labels, and reports are there so that the
  user can decide from a summary and look deeper only when something is
  flagged.
