---
name: ptt-take
description: Take a role or task for this session; conflicts are refused. Arguments: designer (task T0000), integrator, a task ID or name, or none to list ready tasks.
---

# Take a role or a task

Taking is the user's choice: only this command, typed in the session that
takes, approves recording it (an AtE does not); the work itself needs AtE
(rules file).

1. No argument: `<records>/bin/ptt tasks`; show the `ready` tasks and ask
   which one. Stop.
2. `<records>/bin/ptt take <designer|integrator|task>` (`designer` is
   `T0000`; a task by ID `T0007`, `7`, `T0007.1`, or name `wall-distance`).
   If refused (held, draft, blocked), report why and stop; never work around
   it.
3. The tool prints your holder name (`designer-g2`, `integrator-1`,
   `track-T0007`). It is your name from now on: `--as NAME` (the NAME
   argument for `leave` and `whoami`; optional for `record` and `pr-move`,
   added to the commit message), and `session:` in request messages. The
   tool binds it to this session where the agent tool gives a session ID;
   one session holds one role or task. After `/clear` the user continues it
   with `/ptt-resume <name>`: the cleared session does not take again, and
   its writes are refused until it has resumed.
4. Read what you start from, then report what you hold, your supervisor,
   the next step, and every `note:` the tool printed:
   - integrator: `<records>/handoff/integrator.md`, `<records>/bin/pr list`;
   - a task (also `designer`): `<records>/bin/ptt show <N>` (charter,
     amendments, previous holder's `status.md`), then `<records>/bin/ptt
     whoami <name>` for what waits on you. A `design` task makes you the
     designer of its scope: you make and close its subtasks; `T0000`'s
     holder makes the top-level tasks.
5. If the tool notes that `T0000` is not filled in (a project just set up),
   find what exists: earlier handover files in `<records>/handoff/` (not
   `integrator.md`, `notes/`), "superseded" lines in
   `partitur-install-report.md` in the workspace root, the design document,
   earlier briefs. Propose one plan: fill in the charter's placeholders, move
   the earlier handover into `status.md`, record both (on the user's AtE);
   then a draft task per briefed piece of work, each by the user's
   `/ptt-mktask`, naming the brief as its source.
6. While holding a task, record `status.md` (`<records>/bin/ptt record`) at
   least once a day of work, also when the work is on a code branch: a
   supervisor treats seven days without a record as possibly gone.
