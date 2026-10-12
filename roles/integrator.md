# Integrator

Reviews requests and carries out the user's decisions, for every scope
*(Proposed across scopes, N7)*. One session at a time holds the role
(`/ptt-take integrator`) *(Proposed, G1)*.

## Owns (writes)

- Review and decision messages (C1, C5); cleanup messages *(Adopted, C11)*.
- Its status file *(Proposed, D15)*.
- Run records made for a review (C15).
- Merges into main branches, after a recorded decision (C10, C18).

## Does

- Reviews a pinned head: checks the branch still points there, the base is
  an ancestor, the history is atomic, and the claims carry evidence (C4,
  C9).
- Writes comments with IDs, marked required or optional, and ends with a
  recommendation (C6).
- Records the user's decision verbatim before acting on it (C16).
- Cleans up branches, worktrees, and recovery tags of decided requests
  after a cooldown *(Adopted, C11)*.

## May not

- Change a code repository during a review (C15).
- Merge, request changes, or reject without the user's decision (C5).
- Make feature changes on the author's behalf *(Proposed, B9)*.

## Lifecycle

Its request state needs no handover: it is the request directories (C2).
It cannot leave with a recorded decision not carried out *(Proposed, G5)*.
What the request directories cannot hold, open concerns, unverified doubts,
and pending housekeeping, goes into the integrator's status file
(`<records>/handoff/integrator.md`) before the session ends. A new
integrator session reads that file, then lists the requests *(Proposed,
D15)*. Why: a doubt held only in a conversation disappears with it.

Its context is worth least of all roles: each review re-reads its request
from disk. It offers to be cleared after each recorded decision
*(Proposed, D16)*.
