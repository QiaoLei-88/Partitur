---
name: ptt-whoami
description: Show what this session holds and what waits on it, or with "all", who holds what. Only reads; to continue as a holder after /clear, use /ptt-resume. Use for: who am I, what next, who does what. Arguments: none, NAME, all.
---

# Who am I

The command, or an AtE naming these records, approves the records this skill
writes (it writes none); other work needs AtE (rules file).

- No argument: `<records>/bin/ptt whoami`, or `ptt whoami <name>` with the
  holder name this session got from `/ptt-take` or `/ptt-resume`; report
  the role or task, supervisor, charter, every "waits on you" line (leave
  requests, done reports, silent holders), and every "amended since your
  take" line (read the amendment with `ptt show` and say what changes for
  the work), each with a suggested next step. If it holds nothing, say so:
  `/ptt-take` gives it a role or task, `/ptt-resume NAME` continues one.
- `NAME`: `<records>/bin/ptt whoami NAME`: the same report about NAME. It
  does not make this session NAME; that is `/ptt-resume NAME`.
- `all`: `<records>/bin/ptt who` and `<records>/bin/ptt tasks`: who holds
  what, which tasks are ready, blocked, or waiting.
