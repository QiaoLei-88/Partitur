---
name: partitur
description: Partitur — roles, records, and request flow for one user directing several AI agent sessions on a software project. Use when the user asks to install or set up Partitur for a project (run bin/install), when a session must find out its role, what it may write, or how to hand over, or when deciding how work, findings, reviews, and decisions flow between sessions. Taking roles and tasks is the ptt-take, ptt-leave, ptt-whoami, ptt-mktask, ptt-done, and ptt-close skills; requests are ptt-pr-submit, ptt-pr-review, and ptt-pr-cleanup.
---

# Partitur

A partitur is the full score from which every player reads. Here the score
is the project's records: rules, charters, requests, run records. Sessions
come and go; the records carry the work.

## If you are a session in a Partitur project

1. Read the project's rules file. The workspace root links to it as
   `CLAUDE.md` and/or `AGENTS.md`; it lives in the records repository
   (`workspace/` unless the project chose another name, which the rules file
   states). It is authoritative and may override this skill.
2. Know what you hold: a session holds a role or task only by taking it
   (`/ptt-take`), or by continuing as a holder the user names
   (`/ptt-whoami <name>`). Then read your role's page in [roles/](roles/)
   and [roles and tasks](flows/tasks.md).
3. Nothing is authorized until the user says `AtE` for a task (or `AtEiYA`
   and you agree): [authorization](flows/authorization.md).
4. Before writing: one writer per file, records over memory, lasting
   references ([model](model.md), [references](flows/references.md)).
5. Changes reach a main branch only through requests:
   [requests](flows/requests.md) and the `ptt-*` skills.
6. At a quiet point, offer once to be cleared; clearing keeps what you hold:
   [handoff](flows/handoff.md#clearing-context-proposed-d16).

## Installing Partitur for a project

When the user asks for it (that request is the AtE), from the project's
workspace root, the directory holding its code checkouts:

```
<this repository>/bin/install --scope project
```

It detects the agent tools on this machine and installs for those; if the
project should serve a tool that is not installed here, add `--tool all` (ask
the user). The command is *Proposed* (F9, F10): report anything unexpected.
Everything else has a default (see [parameters](parameters.md)); `--repo` is
needed only for checkouts not directly in the workspace root, which can also
be added later as lines in `<records>/pr/repos`. Report the output to the
user, including anything reported as differing.

Then, with the user:

1. **Rules.** If install reports the rules file "not merged" (an existing
   project with its own rules), read the project's rules and Partitur's
   rules block (`templates/rules.md`, between the markers) and list for the
   user every contradiction and overlap, each with your recommendation. Only
   when the user approves, run install again with `--merge-rules`, then
   resolve each contradiction as the user decides, in the project's part of
   the file (outside the block). A new project gets the block at install;
   fill in its "Project Rules": domain rules, and any choice that differs
   from the defaults *(Proposed, T2)*. The block includes rules not yet
   exercised in practice *(Proposed, T1)*: asking the user only what the
   user sees, decides, or uses; a successor checking its handover against
   the records; worker sessions; withdrawing a request; offering to be
   cleared at quiet points; taking roles and tasks with supervised leaving
   (G1-G13). Tell the user, who keeps or drops them.
2. **Repositories.** If install warns that requests name a repository the
   table lacks, or a checkout lies deeper than the workspace root, propose
   the `--add-repo NAME:CHECKOUT:MAIN` line and run it when the user agrees.
3. Fill in `<records>/tasks/open/T0000-design/charter.md`, the root
   designer's charter, then record the records
   repository: `<records>/bin/ptt record -m "install Partitur" <records>`.

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
