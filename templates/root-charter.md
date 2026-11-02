---
task: T0000
kind: design
depends:
designer: user
---

# Task T0000: Design of {{PROJECT}}

The root design task. Its holder is the designer (`/ptt-take designer`,
holder names `designer-g1`, `designer-g2`, ...); the user supervises it.
It is never done, closed, or cancelled: designers leave and successors
take it. Changes to this charter are amendments by the user
(`ptt amend T0000 --as user`). The holder writes `status.md` next to it,
the handover to the next designer. This charter authorizes nothing.

## Goal

The design of {{PROJECT}}, agreed with the user, and the tasks that carry
it out.

## Read first, in order

1. `{{RECORDS}}/PROJECT-RULES.md`, the rules file.
2. `status.md` next to this charter: where the previous designer stopped.
3. The design document ({{WHERE: repository and path}}).
4. `{{RECORDS}}/bin/pr list all`.
5. `{{RECORDS}}/bin/ptt tasks` and `ptt inbox <your holder name>`: the
   tasks, their holders and `status.md`, and what waits on you.

## Scope

- Owns: the design document, the tasks T0001, T0002, ... in
  `{{RECORDS}}/tasks/` (charters, amendments, closing), and `status.md` of
  this task.
- Decides, with the user: design and planning for {{PROJECT}}.

## Out of scope

- Implementation, research in depth, reviewing and merging.
- Design decisions without the user.

## Acceptance

None: this task stays open. A designer leaves when `status.md` lets a
successor continue without this conversation.
