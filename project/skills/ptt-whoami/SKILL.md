---
name: ptt-whoami
description: Show what this session holds and what waits on it; with a holder name, continue as that holder after /clear; with "all", who holds what. Use for: who am I, what next, who does what. Arguments: none, NAME, all.
---

# Who am I

The command, or an AtE naming these records, approves the records this skill
writes; other work needs AtE (rules file).

- No argument, with the holder name this session got from `/ptt-take`:
  `<records>/bin/ptt whoami <name>`; report the role or task, supervisor,
  charter, every "waits on you" line (leave requests, done reports, silent
  holders), and every "amended since your take" line (read the amendment
  with `ptt show` and say what changes for the work), each with a suggested
  next step.
- `NAME` (typically after `/clear`): this session continues as that holder.
  Run `<records>/bin/ptt whoami NAME`, read what it starts from (`/ptt-take`,
  step 4) and its status record, and report where it stands; use NAME as
  before.
- No holder name known: say this session holds nothing; `/ptt-take` gives
  it one, or the user names the holder it continues as.
- `all`: `<records>/bin/ptt who` and `<records>/bin/ptt tasks`: who holds
  what, which tasks are ready, blocked, or waiting.
