---
name: partitur
description: "Partitur, roles, records, and request flow for one user directing several AI agent sessions. Use to install or set up Partitur for a project, or when a session must know its role, what it may write, or how work and decisions flow; the ptt-* skills do the steps."
---

# Partitur

A partitur is the full score from which every player reads. Here the score
is the project's records: rules, charters, requests, run records. Sessions
come and go; the records carry the work.

Command examples use Claude Code's `/ptt-*` notation; in Codex invoke the
same skills as `$ptt-*` (for example `$ptt-take designer`).

## If you are a session in a Partitur project

1. Read the project's rules file, `PROJECT-RULES.md` in the records
   repository (`workspace/` unless the project chose another name, which the
   rules file states); the workspace root links to it as `CLAUDE.md` and/or
   `AGENTS.md`. It is authoritative and may override this skill.
2. Know what you hold: a session holds a role or task only by taking it
   (`/ptt-take`), or by continuing as a holder the user names
   (`/ptt-resume <name>`). Then read your role's page in [roles/](roles/)
   and [roles and tasks](flows/tasks.md).
3. Nothing is authorized until the user says `AtE` for a task (or `AtEiYA`
   and you agree): [authorization](flows/authorization.md).
4. Before writing: one writer per file, records over memory, lasting
   references ([model](model.md), [references](flows/references.md)).
5. Changes reach a main branch only through requests:
   [requests](flows/requests.md) and the `ptt-*` skills.
6. When a `ptt` command prints `nudge:` lines, nudge those sessions as its
   `nudges:` line says; when nudged, do only the read-only part
   ([nudges](flows/handoff.md#nudges-d18)). Codex `queued:` lines
   mean ptt already enqueued the notice: report acceptance, with delivery
   unconfirmed. Report queue errors, including needed sandbox approvals;
   do not repeat the recording command. Pass `carry:` lines to the
   user: they say where to open the inbox when no automatic nudge can reach it.
7. At a quiet point, offer once to be cleared; clearing keeps what you hold:
   [handoff](flows/handoff.md#clearing-context-proposed-d16).

## Installing Partitur for a project

To install, update, or remove Partitur for a project, read
[INSTALL.md](INSTALL.md); a session working in an installed project does
not need it.

## Reading map

- [Model](model.md): concepts, invariants, scopes and nesting, information
  flow.
- Roles: [user](roles/user.md), [designer](roles/designer.md),
  [track](roles/track.md), [worker](roles/worker.md),
  [integrator](roles/integrator.md), [delegate](roles/delegate.md).
- Flows: [roles and tasks](flows/tasks.md),
  [authorization](flows/authorization.md),
  [requests](flows/requests.md), [handoff](flows/handoff.md),
  [evidence](flows/evidence.md), [references](flows/references.md).
- Templates: [task charter](templates/charter.md);
  root design task [charter](templates/root-charter.md) and
  [status](templates/root-status.md), [integrator](templates/integrator.md).
- [Rules index](rules.md): every rule with its ID and label.
