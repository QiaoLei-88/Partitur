# Partitur

A partitur is the full score of a piece: every part, written out, from which
each player reads. Players change; the score stays.

Partitur is a way to run a software project with one human and several AI
agent sessions (Claude Code, Codex, or both). It assigns each session a
role, keeps everything a session needs in files and Git rather than in a
conversation, and lets nothing reach a main branch without a review and the
human's decision. Any session can end at any time, and the next one picks up
from the records.

It is abstracted from the working practice of a real research software
project (the "origin project"), and it keeps track of which of its rules
have actually been used there.

## How it works

Every session starts by taking a role or a task; the records say who holds
what, so any session can be cleared or replaced and the next one continues.

1. In one session: `/ptt-take designer`. It becomes the designer
   (generation 1, or the next generation after a predecessor left).
2. You discuss the work with the designer. `/ptt-mktask` turns the
   discussion into a task draft; `/ptt-mktask release N` makes it ready.
3. In another session: `/ptt-take N`. It becomes that task's holder (a
   track for research, a worker for code, or a sub-designer with its own
   tasks), and the designer is its supervisor.
4. Nothing is changed until you say `AtE` ("approval to execute"), or
   `AtEiYA` ("AtE if you agree") when the session should go ahead only if
   it agrees with you.
5. The holder works on a branch and submits a *request* (`/ptt-pr-submit`);
   the integrator (`/ptt-take integrator`) reviews it (`/ptt-pr-review`);
   you decide, and the decision is recorded before anything is merged.
6. The holder reports the task done (`/ptt-done`); the designer closes it
   (`/ptt-close N`). Leaving early needs the supervisor's approval
   (`/ptt-leave`), and nobody leaves while something waits on them.

`/ptt-whoami` tells a session what it holds and what waits on it, including
any subordinate with no record for seven days (`PTT_STALE_DAYS` changes the
threshold). Conflicts
are refused: a role or task someone holds cannot be taken. The smallest
setup is two sessions, one that works and an integrator
([model](model.md#starting-small)).

Taking roles and tasks, the single install command, and Codex support are
recent and marked *Proposed* in the [rules index](rules.md) until they have
been used in a real project.

## Getting started

Requirements: Git 2.28 or later, Python 3.8 or later, and a system with
symbolic links (Linux or macOS; on Windows, WSL).

1. Clone this repository.
2. Make Partitur known to your agent tool, for all your projects:
   ```
   bin/install --tool claude --scope user     # or codex, or all
   ```
3. In a project's workspace root (the directory holding its code
   checkouts), ask the agent: "install Partitur for this project". It runs
   ```
   bin/install --tool claude --scope project  # or codex, or all
   ```
   which sets up the records repository (`workspace/` by default), the
   rules file, the task and request directories, the tools and skills, the
   designer's and integrator's files, and the links your tool reads. It is
   safe to rerun: existing files are kept, and files Partitur maintains are
   reported if they differ, which shows what an update would bring.
4. With the agent: fill in the rules file's "Project Rules" and the
   placeholders (`{{...}}`) in `workspace/handoff/designer.md`, then record
   the records repository; from then on, every write there goes through
   `ptt`:

   ```
   workspace/bin/ptt record -m "install Partitur" workspace
   ```

   A later Partitur version is brought in by rerunning the install with
   `--update`, which replaces only the files Partitur maintains.
5. Open sessions in the workspace root and let each take its role:
   `/ptt-take designer` in one, `/ptt-take integrator` in another; then
   tasks as the designer makes them ([roles and tasks](flows/tasks.md)).

Start sessions in the workspace root: Codex reads `AGENTS.md` and skills
only from the Git root of its starting directory downwards, and the
workspace root is usually not inside a Git repository. Skills are invoked
as `/ptt-take` in Claude Code and `$ptt-take` in Codex.

## Contents

- [Model](model.md): concepts, invariants, scopes and nesting, information
  flow.
- Roles: [user](roles/user.md), [designer](roles/designer.md),
  [track](roles/track.md), [worker](roles/worker.md),
  [integrator](roles/integrator.md), [delegate](roles/delegate.md).
- Flows: [roles and tasks](flows/tasks.md),
  [authorization](flows/authorization.md), [requests](flows/requests.md),
  [handoff](flows/handoff.md), [evidence](flows/evidence.md),
  [references](flows/references.md).
- [Rules index](rules.md): every rule with its ID and label: *Exercised*
  (used in the origin project), *Adopted* (written into its rules, not yet
  shown in use), or *Proposed* (Partitur's design, untested).
- [Parameters](parameters.md): what you choose at install, and what is
  fixed.
- `bin/install`: the one command you run.
- `project/`: what a project receives (`bin/ptt` for roles and tasks,
  `bin/pr` for requests, `bin/test-run`, the `ptt-*` skills).
- `templates/`: files filled in at install (rules file, request README,
  designer's and integrator's files, the task charter).
- [SKILL.md](SKILL.md): the entry point for agent sessions.
- [Contributing](CONTRIBUTING.md); tests:
  `python3 -m unittest discover -s tests`.

## How Partitur is developed

Partitur evolves alongside the origin project, which remains its proving
ground: a rule becomes Exercised only when a record of real use shows it.
Each milestone gets an independent review by a fresh agent that sees the
records but not the author's reasoning. The evidence behind the labels and
the reviews are kept with the development notes, outside this repository.

## Licence

Partitur is licensed under the GNU General Public License, version 2 only
(SPDX: `GPL-2.0-only`); see [LICENSE](LICENSE).
