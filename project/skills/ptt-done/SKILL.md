---
name: ptt-done
description: As a task's holder, report its acceptance criteria met so that the supervisor can close it. Use when the task's work is merged and its criteria are met.
---

# Report a task done

The command, or an AtE naming these records, approves the records this skill
writes; other work needs AtE (rules file).

1. Check each acceptance criterion of the charter
   (`<records>/bin/ptt show <N>`) against records: merged requests with merge
   commits, run records, notes. A criterion without a record is not met;
   state unknowns and skipped work as such.
2. Write that check, criterion by criterion, into `status.md` and record it:
   `<records>/bin/ptt record -m "task <N>: status" <status.md>`.
3. `<records>/bin/ptt done <N> --as <name> --requests <numbers> --text
   "<one-line summary>"`.
4. Tell the user that the supervisor (named by `<records>/bin/ptt whoami
   <name>`) closes it with `/ptt-close <N>` or reopens it; you hold the task
   until then. The close reaches this session through its inbox (in Claude
   Code with the user's next message; otherwise `/ptt-inbox`), never
   through your own `status.md`, which you wrote before it.
