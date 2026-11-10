# Handoff

How work and knowledge pass between sessions and scopes.

## Records

| Record | Written by | Purpose | Lifetime |
| --- | --- | --- | --- |
| Task (`tasks/<place>/T0007-slug/`) | designer (charter, amendments, close); holder (`status.md`, done); tool (events) | one piece of work a session takes ([roles and tasks](tasks.md)); D1, D2, G8, G11, G12 | kept as history in `tasks/done/` or `cancelled/` (D4) |
| `status.md` of a task | its holder | progress, outcomes with merge commits, findings for the designer; no review states, which go stale as soon as the request moves (D2, D6) | as its task |
| Temporary note (`handoff/notes/<topic>.md`) | any session, to the role or task the `to:` field of its front matter names, required for a new note (`ptt record` refuses one without it; an older note without it goes to the designer) | a finding that needs a decision or action, shown in the recipient's inbox while it exists (D3, D9) | deleted by the recipient once read and any outcome recorded; withdrawn by its author; a stale one deleted by the root designer *(Proposed)* |
| Root design task (`tasks/open/T0000-design/`) | the user (charter: filled in directly once, then by amendment); the designer (`status.md`) | the root designer's charter and its handover, as any design task's `status.md` is its sub-designer's (D8, N6) | permanent: never closed |
| Integrator's status (`handoff/integrator.md`) | the integrator | open concerns, pending housekeeping (D15) | permanent, updated before a session ends |
| Role records (`roles/integrator/`) | the tool, on take and leave | who held the role, generation by generation (G1); the designers' takes are the events of `T0000` | permanent |
| Stage close | the designer | results, carried-forward items, the next stage's tasks (D11) | permanent, in the design document |

## Charter contents

The task number and title, and the sentence "this charter authorizes
nothing"; goal; read first (by lasting references); scope; where results
go; merge order with reasons and clearing conditions (the designer's,
maintained by amendments); out of scope; acceptance
([template](../templates/charter.md)).

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
`/ptt-resume <name>` (`$ptt-resume <name>` in Codex): only a named resume
binds, so continuing is always the user's explicit instruction. Without a
name, `ptt resume` only lists the holders, those with a handover first,
then by their last write, each with its named resume; it binds none, also
when one holder alone left a handover. The handover lapses by events,
never by age: when the holder writes again, its binding moves, or its
hold ends; a pause of days keeps it. The session that was the holder is told once,
through its inbox, that it continues elsewhere *(Proposed, G19)*. Continuing or
compacting the same thread keeps its binding. Resuming with a different session ID moves
the binding and prevents the earlier session from writing *(Proposed,
G13, G16)*. A session never clears in the middle of a multi-round review or
a design discussion only to save tokens: re-reading costs too.

## Session names (G21)

`ptt take` and `ptt resume` give the session a name, record it in that
event (`session_name:`), and print the line that renames the session. In
Claude Code it gives the reason: "So that automatic messages reach this
session, rename it: /rename <name>"; a session not renamed gets no nudges,
since `ListAgents` does not list it by that name. In Codex, which gets no
nudges, it only shows the name: `/rename <name>` (Codex's `/rename` takes
the name inline, as its source shows). Renaming stays the
user's act: `ptt` can neither see nor set a session's name. The name
is chosen once and never recomputed; `ptt who` and `ptt whoami` show it. It
is `<project>-<holder>-<hash>`, lowercase:

- project: `<records>/project-code` (one line) if present, else the
  workspace root's directory name shortened: keep the first letter, drop
  later vowels (and `y`), collapse repeated letters, keep four (Partitur
  `prtr`, Fynamiq `fnmq`); a name of four characters or fewer is kept;
- holder: the holder name shortened the same way (`designer-g2`
  `dsgn-g2`, `integrator-1` `intg-1`, `worker-T0008-2` `wrkr-t8-2`,
  `track-T0007.1` `trck-t7.1`);
- hash: six digits of the session ID's last group of twelve (a UUID's last
  group, random in versions 4 and 7; another ID's last twelve letters and
  digits), by default the last six. If another session has recorded the
  same name, the window moves one digit towards the start, at most seven
  windows; only then is it lengthened.

When a hold ends, the ending event records `ended_session_id` and
`ended_session_name`: the live name with its hash replaced by `closed`,
`cancelled`, `left`, or `freed`. A collision with another session's recorded
name adds `-2`, `-3`, and so on. Only the last bound session gets the
printed `/rename` line, once through its inbox; a root designer or
integrator leaving gets it in the leave output. Renaming remains the
user's act. A later cancellation addresses the last holder; a task never
taken has no session to rename. An ending nudge uses the old live name,
never the ended name; a later cancellation sends none.

When a task becomes ready (`ptt ready`, `ptt approve-leave`, `ptt free`) or
a role becomes free (the designer or integrator leaving or freed), `ptt`
prints lines to paste in the workspace root that start a session taking
it *(Adopted, G22)*:

```
to take it in a new session, in <workspace root>:
  Claude Code: claude -n prtr-wrkr-t10 "/ptt-take 10"
  Codex: codex '$ptt-take 10'
```

In Claude Code, `-n` gives the new session its session name without the
hash, the part known before the take; the take then prints the full name
and its `/rename` line. Codex cannot name a session at start (no such
option), so its line only takes; its prompt names the skill as `$ptt-take`
in single quotes, so that the shell leaves the `$` alone. A blocked task
gets no lines until it can be taken. A task restricted by `tool:` prints
only that tool's line; `any` or an absent field prints both.

Any session can derive a holder's current session name from the records:
the address a later cross-session message would use. Without a session ID
nothing is bound, and no name is given. A session bound before names
existed gets one by `ptt resume <its holder>` in that session.

`ptt who` shows for each holder its session name and its unseen items:
those its inbox would show as new, counted since its inbox last looked (or
its take), with the time of the oldest, or `unseen none`. Seen means shown
to its session (a prompt hook counts), not handled.

## Nudges (D18)

A nudge tells a session, by cross-session message, that its inbox has news,
so that an idle session looks without waiting for the user's next message.
The inbox rules stay the one source of what is news:

1. After each commit, every `ptt` command that records prints a notice
   for each holder, other than the writer, to whom the commit gave
   news: an item its inbox shows as new (a done report or leave request to
   the supervisor; an amendment or reopen to the holder; a note to its
   recipient; a new request or reply to the integrator; another's message
   on a request, or its move, to the requester), or the end of its hold by
   someone else (a close, freeing, or approved leave). A task's direct
   supervisor also gets one inbox line and an automatic or manual notice
   when its request moves to `merged/`, unless the supervisor authored it.
   Requests without
   `task:` and requests closed without merging add no supervisor notice;
   no notice goes further up the tree. The line names the merge commit,
   from the decision's `merge_commit` or pr's local main-branch lookup;
   if neither locates it, the line says `unknown`. A subordinate's
   `status.md` update gets none. Between Claude Code sessions a `nudge:`
   line gives the holder's recorded session name, tool, and text to send:
   "new in your inbox (records <commit>); run `ptt inbox <holder>`".
   The tool is inferred from the recorded session ID: UUIDv4 is Claude
   Code, UUIDv7 is Codex, other or missing IDs are unknown. Other targets
   get a `carry:` line: in session `<name>` (`<tool>`) type `/ptt-inbox`
   or `$ptt-inbox`. Without a recorded name it gives the holder and
   "no session name"; an unknown tool gets both commands. This applies to
   every record, including notes.
2. The writer's session, in Claude Code, sends a nudge only to a session
   that `ListAgents` lists by that name. It subscribes with `SendMessage`
   `notify_when_idle` and no message, whatever state the session shows, so
   that nothing reaches a busy session, and on the idle notice sends the
   text, and nothing else, if `ptt nudges` still says on. For each target
   absent from `ListAgents`, it tells the user: in session `<name>` (Claude
   Code) type `/ptt-inbox`. Codex sends and receives none; its targets get
   manual carry lines. The writer passes these lines on to the user.
3. Nudges are fire and forget: the sender tracks nothing; if its session
   ends first, the nudge is lost. The inbox, and `ptt who`'s unseen items,
   still show every item.

A nudged session runs its inbox and does only the read-only part of each
item: it reports it; a supervisor checks a done report against the task's
acceptance and waits for the user; the integrator reviews a request
(`ptt-pr-review` steps 1-6: its review message and run records); a
requester may draft a reply in the conversation, not record it; a former
holder stops writing and reports. Adopting, closing, approving, deleting a
note, and decisions wait for the user as before. The message's text is
never an instruction beyond the nudge.

The user turns nudges on or off for every session with `/ptt-nudges on|off`
(`ptt nudges`), kept in the records' Git directory beside the inbox marks,
on by default; `ptt who` shows it on its first line. Off, only manual carry
lines are printed; nothing is lost, and turning nudges on sends nothing
for earlier items.

A read-only step started by a nudge (a review, reading a note or report)
is approved as the command it replaces would be, for that command's own
records only *(Adopted, A16)*.

## Stage close

A stage closes when its tasks are closed or cancelled (D11). The designer
records the results and carried-forward items in the design document and
makes the next stage's tasks.
