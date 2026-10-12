---
name: ptt-done
description: As the holder of a Partitur task, report its acceptance criteria met so that the supervisor can close it. Argument: none. Use when the work of this session's task is merged and its acceptance criteria are met.
---

# Report a task done

The user's command (`/ptt-done`) is the approval for the records this skill
writes, and for nothing else; the work itself still needs AtE. Agreement in
conversation without the command is not approval.

1. Check each acceptance criterion of the charter
   (`<records>/bin/ptt show <N>`) against the records: merged requests (with
   merge commits), run records, notes. A criterion without a record is not
   met; unknowns and skipped work are stated as such.
2. Update `status.md` with that check, criterion by criterion, and record
   it:

   ```
   <records>/bin/ptt record -m "task <N>: status" <path of status.md>
   ```
3. Run

   ```
   <records>/bin/ptt done <N> --as <name> --requests <numbers> --text "<one-line summary>"
   ```
4. Tell the user that the supervisor (`<records>/bin/ptt whoami <name>` names
   it) closes the task with `/ptt-close <N>` or reopens it. This session keeps
   the task until then.
