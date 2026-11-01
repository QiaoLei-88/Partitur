# Roles and tasks (G1-G18; *Proposed: G5-G7, G10, G14, G15, G18*)

How a session gets its role, how work is cut into tasks, and how both pass
from session to session. Every step is a command the user runs in a
session; the tool `<records>/bin/ptt` records it as a file and commits it at
once, so the records always say who holds what.

## Lifecycle

```
designer:  /ptt-take designer ─► /ptt-mktask ─► /ptt-mktask release N
                                                        │
any session:                         /ptt-take N ◄──────┘
                                         │
holder:     work ─► /ptt-pr-submit ─► (integrator reviews, user decides)
                                         │
holder:     /ptt-done ─► supervisor: /ptt-close N (or reopen)
```

| State | Meaning | Next |
| --- | --- | --- |
| draft | made by the designer, editable | release (`/ptt-mktask release N`) |
| ready | released, nobody holds it | take (`/ptt-take N`) |
| blocked | released, but a task it depends on is not closed | waits |
| held | a session holds it | work; done; leave (with approval) |
| closed | the supervisor accepted the done report; the hold ends | moved to `tasks/done/` |
| cancelled | no longer wanted, nobody held it | moved to `tasks/cancelled/` |

## Rules

1. **Take, never assume.** A session holds the integrator role or a task
   only by taking it; the designer is the holder of the root design task
   `T0000` (`/ptt-take designer`). The tool prints the holder name
   (`designer-g2`, `integrator-1`, `track-T0007`, `design-T0007.1`, and
   `track-T0007-2` for a task's second holder), which is its `--as` name and
   its `session:` in every message (G1, G2).
2. **Conflicts are refused.** A held role or task cannot be taken; a second
   simultaneous take loses. Nothing is overridden silently (G1).
3. **Taking is not approval to work.** The user's command records the role;
   writes still need the user's AtE (A2).
4. **Supervision is a tree.** A top-level task's (`T0007`) supervisor is
   the designer, the holder of `T0000`; the holder of a `design` task is the
   designer of its subtasks (`T0007.1`, `T0007.2`, ...); the designer's and
   integrator's supervisor is the user (G3, G10). `T0000` is never done,
   closed, or cancelled, and has no dependencies, nor does any task depend
   on it. The user fills in its charter at install; after that it changes
   only by the user's amendment.
5. **Leaving needs the supervisor.** A task holder asks to leave; its
   supervisor approves after reading `status.md`. The root designer (holder
   of `T0000`) and the integrator leave on the user's command (G4).
6. **Nobody leaves while anything below them is unclear:** a leave request
   or done report waiting, or a holder with no record for seven days,
   anywhere in the subtree; the integrator also not with a recorded decision
   not carried out. A design task with unfinished subtasks cannot be
   cancelled (G5).
7. **The leader repairs a gap.** A subordinate with no record for seven days
   is listed by `/ptt-inbox` for its supervisor, who checks on it and, if it
   is gone, frees the task; `status.md` shows where it stood. A holder
   therefore commits `status.md` in the records repository at least once a day
   while it works, also when the work itself is on a code branch. Only the
   user frees the designer (`T0000`, with `--force` while it has recent
   records) or the integrator role, and the user acts (`--as user`)
   for any task whose supervisor is vacant, for example after a sub-designer
   left (G6, G7).
8. **A charter is frozen once released**; changes are amendments, recorded
   as events. The holder writes only `status.md` (G11, G12).
9. **Clearing does not change the holder.** The role or task stays
   recorded; after `/clear`, the user names the holder the fresh session
   continues as (`/ptt-resume <name>`, or `/ptt-resume` alone for the
   holder that left a handover at its quiet point, G19), and it picks up from
   the records.
   Leaving is for handing the work to another session (D16, G13).
10. **A holder is bound to one session.** Where the agent tool gives a
    session ID (Claude Code and Codex do), taking and resuming record it
    with the holder name. A write as a holder bound to
    another session is refused, and so is any write from a session whose
    holder has resumed elsewhere; one session holds one role or task. An
    unbound holder (taken without a session ID, or before Partitur bound
    holders) is not checked until it resumes (G16).

## Records

```
<records>/tasks/
  charter-template.md
  open/ done/ cancelled/
    T0000-design/       the root design task: charter by the user, status.md
                        the designer's handover
    T0007-wall-distance/
      charter.md          the designer's, frozen at release
      status.md           the holder's: done, open, where it stands
      0001-release.md     events, each written once:
      0002-take.md          release, take, leave-request, leave, done,
      0003-leave-request.md reopen, amend, resume, close, cancel
      ...
<records>/roles/integrator/ 0001-take.md (integrator-1), 0002-leave.md, ...
```

A task's ID is `T`, its number, and its slug: `T0007-wall-distance`, the
directory name. It never changes once the task exists; commands accept the
short forms `T0007`, `0007`, `7`, or the slug alone while it is unique among
unfinished tasks (G10).

A task's state is derived from its events, as a request's is from its
messages; there is no state file to go stale (C2).

## Commands

| Command | Who | Runs |
| --- | --- | --- |
| `/ptt-take [designer\|integrator\|task]` | any session | `ptt take`; a task by ID (`T0007`, `0007`, `7`, `T0007.1`), full name (`T0007-wall-distance`), or slug; without argument `ptt tasks` |
| `/ptt-whoami [name\|all]` | any session | `ptt whoami`: who this session is (reads only); `all`: `ptt who`, `ptt tasks` |
| `/ptt-inbox [name]` | any holder | `ptt inbox`: what is new since the holder last looked, and what waits on it |
| `/ptt-resume [NAME]` | a cleared or fresh session | `ptt resume`: continue as NAME, or without NAME the holder that left a handover (`ptt handover`), bound to this session |
| `/ptt-mktask`, `release N`, `amend N` | designer | `ptt mktask`, `ptt ready`, `ptt amend` |
| `/ptt-done` | holder | `ptt done` |
| `/ptt-close N`, `reopen N`, `cancel N` | supervisor | `ptt close`, `ptt reopen`, `ptt cancel` |
| `/ptt-leave`, `approve N`, `free N\|ROLE` | holder; supervisor; supervisor or user | `ptt leave`, `ptt approve-leave`, `ptt free` |
| `/ptt-pr-submit`, `/ptt-pr-draft-reply`, `/ptt-pr-reply`, `/ptt-pr-review`, `/ptt-pr-cleanup` | holder; integrator | requests ([requests](requests.md)) |

In Codex the commands start with `$` instead of `/`.

## Limits

- **Names are not authenticated.** `--as NAME` and `--as user` are taken at
  their word; the records show who did what, and the user's commands are
  the only authority (A2). This guards against mistakes, not against a
  session lying.
- **Sessions are bound only where the tool gives an ID.** Claude Code and
  Codex do; in a plain terminal without an ID, holders are unbound, and
  naming one holder in one session at a time is the user's part. The binding
  guards against mistakes, not against a session lying about its ID.
- **Notices are pulled, except through the prompt hook.** `ptt inbox`
  lists what changed in the records for a holder since it last looked: a
  subordinate's `status.md`, done report, or leave request, an amendment, a
  note to the designer, a new review or decision on its request, and for the
  integrator a new request or reply; and, once, to the session last bound
  to a holder whose hold someone else ended (a close, an approved leave, a
  freeing). In Claude Code and Codex (once trusted), install's prompt hook
  runs it before each user message, so a bound holder sees it with the
  user's next message; without the hook the holder runs `/ptt-inbox`, and
  the user carries the notice as before (D12, G17). A session that receives no
  message sees nothing until it does. Holder changes are not in it, so a
  session that names who holds a role or task, or who acts next, runs
  `ptt who` at that moment rather than trusting an earlier answer (G18).
- **One shared records directory.** The lock that keeps concurrent commands
  consistent is a directory in the records repository's Git directory, so
  it works for sessions on every machine that shares that directory, as
  long as creating a directory there is atomic. A lock left by a killed
  command is removed when its process is known to be gone: automatically on
  the same machine, by `ptt unlock` on the machine that held it, or, if
  that machine no longer exists, by the user's `ptt unlock --force`, which
  also removes a broken lock that names no owner. Its age never decides
  (F11).
- **One gate for the records repository.** Every write to it goes through
  `ptt` (`ptt record` for request messages, `status.md`, and `handoff/integrator.md`),
  which commits exactly its paths under the lock all sessions share. Git
  commands run by hand in the records repository while sessions work
  (stash, checkout, a manual commit) are outside this guarantee and can mix
  changes; do them only when no session is writing (F11).

## Recovery

A `ptt` command undoes its own change when it fails. If it is killed
mid-way, files may be left changed but not recorded; `ptt tasks` then lists
them under "uncommitted in the records repository". Look at them with
`git -C <records> status` and decide:

- **Keep the change** (the command had done its work, only the commit is
  missing): record every listed path, both sides of a move:
  `<records>/bin/ptt record -m "<what it was>" <paths>`.
- **Drop the change**: restore the recorded state of the listed paths with
  `git -C <records> reset -q -- <paths>` and
  `git -C <records> checkout -- <paths>`, then delete what is still
  untracked. Do this only while no session is writing (F11).

Then run the command again if it is still wanted.
