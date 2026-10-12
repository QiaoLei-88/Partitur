---
name: ptt-take
description: Take a Partitur role or task for this session. Arguments: designer (the root design task T0000), integrator, a task ID or name, or none to list the tasks ready to take. Conflicts are refused. Use when the user asks this session to become the designer or integrator, or to take a task.
---

# Take a role or a task

The records repository is `<records>/`; its tool is `<records>/bin/ptt`.
Taking is the user's choice for this session, so the user's command is the
approval to record it. It does not authorize the work itself: that still
needs the user's AtE.

1. No argument: run `<records>/bin/ptt tasks`, show the tasks whose state is
   `ready`, and ask the user which one to take. Stop.
2. Run `<records>/bin/ptt take <designer|integrator|task>`. `designer` is
   the root design task `T0000`. A task is given by ID (`T0007`, `7`,
   `T0007.1`) or by name (`wall-distance`). If it is refused (held, draft,
   blocked), report why and stop; never work around a refusal.
3. The tool prints this session's holder name, for example `designer-g2`,
   `integrator-1`, or `track-T0007`. Remember it: it is your `--as NAME` for
   every `ptt` command and your `session:` in every request message. A
   cleared session continues as the same holder when the user names it
   (`/ptt-whoami <name>`); it does not take again.
4. Read what the role starts from, and report to the user what you hold,
   your supervisor, and the next step:
   - integrator: `<records>/handoff/integrator.md`, then
     `<records>/bin/pr list`;
   - task, including `designer`: `<records>/bin/ptt show <N>`: its charter,
     amendments, and the previous holder's `status.md`, if any; then
     `<records>/bin/ptt whoami <name>` for what waits on you. A `design`
     task makes you the designer of its scope: you make and close its
     subtasks. The root designer (`T0000`) makes the top-level tasks.

   Report every `note:` line the tool printed to the user.
5. If the tool notes that `T0000` is not filled in (a project just set
   up), find what the project already has: earlier handover files in
   `<records>/handoff/` (other than `integrator.md` and `notes/`), lines
   reported "superseded" in `partitur-install-report.md` in the workspace
   root, the design document, and earlier work briefs. Propose one plan to
   the user: fill in the charter's placeholders, move the earlier handover
   into `status.md`, and record both; then, for each piece of work already
   briefed, a draft task (`/ptt-mktask`, naming the brief as its source).
   Carry out the first part on the user's AtE; each draft task is the
   user's `/ptt-mktask`.
6. While holding a task, record `status.md` (`<records>/bin/ptt record`) at
   least once a day of work, also when the work itself is on a code branch:
   a supervisor treats a holder with no record for seven days as possibly
   gone.
