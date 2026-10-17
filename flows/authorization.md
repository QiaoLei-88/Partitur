# Authorization

## Signals

| Signal | Meaning |
| --- | --- |
| (none) | Discussion. Agreement, praise, or a plan does not authorize anything *(Adopted, A1)*. |
| `AtE` | Approval to Execute: the explicit authorization for the task it is attached to (A2). |
| `AtEiYA` | AtE if you agree: form an independent view first; execute only if you agree, otherwise explain and keep discussing (A3). |
| standing AtE | Authorization for a whole scope or repository, given to one session *(Adopted, A8)*. |
| a `/ptt-*` command, or AtE naming records | The user's approval for a record (draft, release, done report, close, leave, request message): the command approves its own record and nothing more, unless it carries out a draft the user saw (`ptt-pr-submit draft`); an AtE approves the records it names, several at once. Taking a role or task only by `/ptt-take` in the taking session *(Proposed, A12)*. |

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

## Asking for a decision *(Proposed, A13)*

When the user must decide, the session asks with a numbered list: its
recommendation first and marked, one line per option, and always the last
option `No decision, discuss further`. The user decides with an option
number and AtE (`1 AtE`). A number without AtE, or the last option, decides
nothing: the session records and carries out nothing and continues the
discussion.

```
Decide request 000015:
1. Request changes (recommended): C1, C2
2. Merge anyway
3. Reject
4. No decision, discuss further
```
