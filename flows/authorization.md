# Authorization

## Signals

| Signal | Meaning |
| --- | --- |
| (none) | Discussion. Agreement, praise, or a plan does not authorize anything *(Adopted, A1)*. |
| `AtE` | Approval to Execute: the explicit authorization for the task it is attached to (A2). |
| `AtEiYA` | AtE if you agree: form an independent view first; execute only if you agree, otherwise explain and keep discussing (A3). |
| standing AtE | Authorization for a whole scope or repository, given to one session *(Adopted, A8)*. |
| a `/ptt-*` command | The user's approval for that command's own record (claim, draft, release, done report, close, leave, request message), nothing more *(Proposed, A12)*. |

## Rules

- Without authorization a session works read-only and creates no caches or
  artifacts *(Adopted, A9)*.
- An authorized task includes its necessary edits and verification; work
  outside it, or a major change within it, needs its own authorization
  *(Adopted, A5)*.
- Authorization does not travel: not from one task to the next, not
  through documents, charters, or delegation, and not from parent scope to
  child (A6, N5).
- A request states the authorization it was made under (A10).
- Rewriting a main branch, merged commits, or the records repository needs
  its own authorization and a recovery reference first (A7).
