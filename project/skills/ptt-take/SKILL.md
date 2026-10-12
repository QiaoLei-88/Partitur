---
name: ptt-take
description: Take a Partitur role or task for this session. Arguments: designer, integrator, a task number or name, or none to list the tasks ready to take. Conflicts are refused. Use when the user asks this session to become the designer or integrator, or to take a task.
---

# Take a role or a task

The records repository is `<records>/`; its tool is `<records>/bin/ptt`.
Taking is the user's choice for this session, so the user's command is the
approval to record it. It does not authorize the work itself: that still
needs the user's AtE.

1. No argument: run `<records>/bin/ptt tasks`, show the tasks whose state is
   `ready`, and ask the user which one to take. Stop.
2. Run `<records>/bin/ptt take <designer|integrator|task>`. A task is given
   by number (`7`, `0007`, `0007.1`) or by name (`wall-distance`). If it is
   refused (held, draft, blocked), report why and stop; never work around a
   refusal.
3. The tool prints this session's holder name, for example `designer-g2`,
   `integrator-1`, or `track-0007`. Remember it: it is your `--as NAME` for
   every `ptt` command and your `session:` in every request message. A
   cleared session continues as the same holder when the user names it
   (`/ptt-whoami <name>`); it does not take again.
4. Read what the role starts from, and report to the user what you hold,
   your supervisor, and the next step:
   - designer: `<records>/handoff/designer.md`, then
     `<records>/bin/ptt whoami <name>` for what waits on you;
   - integrator: `<records>/handoff/integrator.md`, then
     `<records>/bin/pr list`;
   - task: `<records>/bin/ptt show <N>`: its charter, amendments, and the
     previous holder's `status.md`, if any. A `design` task makes you the
     designer of its sub-scope: you make and close its subtasks.
5. While holding a task, record `status.md` (`<records>/bin/ptt record`) at
   least once a day of work, also when the work itself is on a code branch:
   a supervisor treats a holder with no record for seven days as possibly
   gone.
