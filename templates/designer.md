# Designer of {{PROJECT}}

The root designer's charter and handover file. The session holding the role
(`/ptt-take designer`) owns it; a new designer session starts here, and an
outgoing one updates it before it stops writing. This file authorizes
nothing.

## Role

- Owns: the design document ({{WHERE: repository and path}}), the tasks of
  its scope in `{{RECORDS}}/tasks/` (charters, amendments, closing), and
  this file.
- Decides, with the user: design and planning for {{PROJECT}}.
- Not this role's work: implementation, research in depth, reviewing and
  merging.

## Read first, in order

1. `{{RECORDS}}/CLAUDE.md`, the rules file.
2. The design document, at {{COMMIT}} or later.
3. `{{RECORDS}}/bin/pr list all`.
4. `{{RECORDS}}/bin/ptt tasks` and `ptt whoami <your holder name>`: the
   tasks, their holders and `status.md`, and what waits on you.

## State

- Checkouts and branches: {{REPOSITORY, main branch at COMMIT; open
  development branches and their requests}}.
- Decided since the last handover: {{REQUESTS with outcome and merge
  commit}}.
- Verification: {{COMMANDS and run ids that show the current state}}.
- Not adopted, waiting: {{PROPOSALS and what they wait for}}.
- Waiting on the user: {{INPUTS}}.
- Owed by other sessions: {{ITEMS}}; check them in the records, not here.

## Agreed but not yet in the design document

{{DECISIONS the user agreed that no record holds yet, with their wording;
or "None"}}. An agreement held only in a conversation is lost at handover.

## Incoming findings to integrate

{{FINDINGS in tasks' status.md or notes that are not yet design decisions,
each with where it is}}.

## Next

{{STEPS, in order, as the outgoing session would take them}}

## Status

(Updated by the designer: what this session decided with the user, by
record, and where it stopped.)
