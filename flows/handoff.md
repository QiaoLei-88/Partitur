# Handoff

How work and knowledge pass between sessions and scopes.

## Records

| Record | Written by | Purpose | Lifetime |
| --- | --- | --- | --- |
| Task (`tasks/<place>/T0007-slug/`) | designer (charter, amendments, close); holder (`status.md`, done); tool (events) | one piece of work a session takes ([roles and tasks](tasks.md)); D1, D2, G8, G11, G12 | kept as history in `tasks/done/` or `cancelled/` (D4) |
| `status.md` of a task | its holder | progress, outcomes with merge commits, findings for the designer; no review states, which go stale as soon as the request moves (D2, D6) | as its task |
| Temporary note (`handoff/notes/<topic>.md`) | any session, to the role or task its `to:` line names (the designer without one) | a finding that needs a decision or action, shown in the recipient's inbox while it exists (D3, D9) | deleted by the recipient once read and any outcome recorded; withdrawn by its author; a stale one deleted by the root designer *(Proposed)* |
| Root design task (`tasks/open/T0000-design/`) | the user (charter: filled in directly once, then by amendment); the designer (`status.md`) | the root designer's charter and its handover, as any design task's `status.md` is its sub-designer's (D8, N6) | permanent: never closed |
| Integrator's status (`handoff/integrator.md`) | the integrator | open concerns, pending housekeeping (D15) | permanent, updated before a session ends |
| Role records (`roles/integrator/`) | the tool, on take and leave | who held the role, generation by generation (G1); the designers' takes are the events of `T0000` | permanent |
| Stage close | the designer | results, carried-forward items, the next stage's tasks (D11) | permanent, in the design document |

## Charter contents

The task number and title, and the sentence "this charter authorizes
nothing"; goal; read first (by lasting references); scope; where results
go; out of scope; acceptance ([template](../templates/charter.md)).

## Handover

The outgoing designer updates its design task's `status.md` (`T0000` for
the root designer): what it decided, what is open, what others owe, what comes next, all by lasting references
([references](references.md)). The incoming session reads it, checks the
state against the records rather than trusting it, reports differences, and
asks the user what comes first *(Proposed, D13)*. The outgoing session then
stops writing.

## Succession of other roles (D15)

A track or worker leaves its task with the supervisor's approval, after
bringing `status.md` up to date: what is done, what is open, where it stands.
The next session takes the task again and continues from it; a worker's
successor continues the same branch ([roles and tasks](tasks.md)). The
integrator's request state is the request directories (C2); its open concerns,
unchecked doubts, and pending housekeeping go into its status file, from
[templates/integrator.md](../templates/integrator.md).

## Clearing context *(Proposed, D16)*

A session's context is a cost, not a record: everything that matters is in
files. At a quiet point a session offers, once, to be cleared:

| Role | Quiet point |
| --- | --- |
| Integrator | after a decision is recorded, or when nothing waits for review |
| Track or worker | after one of its requests is decided and its status updated |
| Designer | only at a stage boundary, through its design task's `status.md` and a new session |

It offers only after substantial work since its last clear, and only when
all three hold:

1. nothing it is writing is uncommitted;
2. its open concerns are in its status record (its task's `status.md`,
   or the integrator's file);
3. nothing was agreed with the user only in conversation.

The offer is one short message, for example:

```
Quiet point: decision on request 14 recorded; nothing waiting for review.
Committed: yes. Open concerns: in handoff/integrator.md. Unrecorded
agreements: none. Clear now if you like (/clear).
```

With the offer the session leaves a handover (`ptt handover <name>`), a
local marker, not a record. The user's `/clear`, or a new session, is
approval of the offer; ignoring it means continue. Clearing does not
release the holder. In Claude Code, `/clear` starts a fresh session ID; in
Codex, so does a fresh chat or fork. The fresh session continues with
`/ptt-resume` (`$ptt-resume` in Codex) and no name: the holder that left the
handover. Without one, or with several, it lists the holders by their last
write and the user names one. The handover lapses by events, never by age:
when the holder writes again, its binding moves, or its hold ends; a
pause of days keeps it. The session that was the holder is told once,
through its inbox, that it continues elsewhere (G19). Continuing or
compacting the same thread keeps its binding. Resuming with a different session ID moves
the binding and prevents the earlier session from writing *(Proposed,
G13, G16)*. A session never clears in the middle of a multi-round review or
a design discussion only to save tokens: re-reading costs too.

## Stage close

A stage closes when its tasks are closed or cancelled (D11). The designer
records the results and carried-forward items in the design document and
makes the next stage's tasks.
