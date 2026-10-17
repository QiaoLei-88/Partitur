---
name: ptt-whoami
description: Show who this session is in a Partitur project (holder name, role or task, supervisor, session binding), or with "all", who holds what. Only reads; what is new or waits is /ptt-inbox; continuing a holder after /clear is /ptt-resume. Arguments: none, NAME, all.
---

# Who am I

The command, or an AtE naming these records, approves the records this skill
writes (it writes none); other work needs AtE (rules file).

- No argument: `<records>/bin/ptt whoami` (the holder bound to this
  session), or `ptt whoami <name>` with the holder name this session got from
  `/ptt-take` or `/ptt-resume`; report the holder name, role or task,
  supervisor, charter, and whether this session is bound to it. If it holds
  nothing, say so: `/ptt-take` gives it a role or task, `/ptt-resume NAME`
  continues one.
- `NAME`: `<records>/bin/ptt whoami NAME`: the same about NAME. It does not
  make this session NAME; that is `/ptt-resume NAME`.
- `all`: `<records>/bin/ptt who` and `<records>/bin/ptt tasks`: who holds
  what, which tasks are ready, blocked, or waiting.
