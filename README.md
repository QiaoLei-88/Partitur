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

## Principles

Six ideas decide everything else; when in doubt, ask which one applies.

1. **You decide.** Sessions discuss, propose, and review; nothing is
   written until you say `AtE` ("approval to execute"), or `AtEiYA` ("AtE
   if you agree") when the session should go ahead only if it agrees.
   Running a `/ptt-*` command is your approval for that command's own
   record, nothing more.
2. **Take a role before working.** A session is the designer, the
   integrator, or the holder of one task, and only because it took that
   role with a command. A role someone holds cannot be taken.
3. **Records, not memory.** What matters is in files in the records
   repository, so a session can be cleared or replaced at any time and the
   next one continues from them.
4. **Review recommends, you decide.** Code reaches a main branch only
   through a request: the integrator reviews it, you decide, and the
   decision is recorded before the merge.
5. **Supervisors answer for what is below them.** The designer supervises
   the tasks it made; a holder leaves only with its supervisor's approval;
   nobody leaves while something below them waits; a supervisor notices a
   silent holder and frees its task.
6. **Labels say how sure we are.** Decisions are Agreed, Proposed, or Open;
   evidence is Source, Inferred, Tested, or Unknown; each of Partitur's own
   rules says whether it has been used in practice ([rules index](rules.md)).

## Which command when

| You want to... | In which session | Command |
| --- | --- | --- |
| start the design, or take it over | any free session | `/ptt-take designer` |
| turn a discussion into a task | the designer | `/ptt-mktask`, then `/ptt-mktask release N` |
| have a session work on a task | any free session | `/ptt-take N` (or the task's name) |
| know what a session holds and what waits on it | any | `/ptt-whoami`; `/ptt-whoami all` for everyone |
| continue a role after `/clear` | the cleared session | `/ptt-whoami <holder name>` |
| submit finished work for review | the task holder | `/ptt-pr-submit` |
| review and carry out your decision | the integrator (`/ptt-take integrator`) | `/ptt-pr-review` |
| report a task done / accept it | holder / its supervisor | `/ptt-done` / `/ptt-close N` |
| stop holding a role or task | that session | `/ptt-leave` (a task needs the supervisor's `/ptt-leave approve N`) |
| clean up merged branches | the integrator | `/ptt-pr-cleanup` |

In Codex, commands start with `$` instead of `/`. For anything not in this
table, ask a session: it reads Partitur's documents and explains, for
example "how does leaving a task work?" or "what does the integrator do?".

## Getting started

Requirements: Git 2.28 or later, Python 3.8 or later, and a system with
symbolic links (Linux or macOS; on Windows, WSL); Claude Code, Codex, or
both.

1. **Clone** this repository anywhere, for example `~/partitur`.
2. **Once per machine**, make Partitur known to your agent tools:

   ```
   ~/partitur/bin/install --scope user
   ```

   It detects Claude Code and Codex and reports what it found;
   `--tool claude`, `codex`, or `all` chooses explicitly.
3. **Once per project**, in its workspace root (the directory that holds
   the project's code checkouts), start a session and ask: "install
   Partitur for this project". The session runs

   ```
   ~/partitur/bin/install --scope project
   ```

   and reports what it created: the records repository `workspace/` with
   the rules file, task and request directories, tools and skills, the
   designer's and integrator's files, and the links your tools read. It
   lists the code repositories it found; one deeper down is added as a line
   in `workspace/pr/repos`.
4. **Fill in two files** with the session: the "Project Rules" at the end
   of `workspace/CLAUDE.md` (your domain's rules), and the placeholders in
   `workspace/handoff/designer.md`. Then record them:

   ```
   workspace/bin/ptt record -m "install Partitur" workspace
   ```

   From now on every write in `workspace/` goes through `ptt`.
5. **Open sessions** in the workspace root and give each its role: in one,
   `/ptt-take designer`; in another, `/ptt-take integrator`. Discuss the
   first piece of work with the designer and make it a task; in a third
   session, `/ptt-take` it.

Always start sessions in the workspace root: Codex reads `AGENTS.md` and
skills only from the Git root of its starting directory downwards, and the
workspace root is usually not inside a Git repository.

To bring a project up to a newer Partitur, pull this repository and rerun
step 3's command with `--update`. A manifest in `workspace/.partitur/`
records what was installed, so the update replaces what is outdated and
removes what Partitur no longer ships, but leaves your rules, your records,
and any file you changed (`--force` replaces those). `--uninstall` removes
what was installed the same way; `--scope user --uninstall` removes the
link for your tools.

Taking roles and tasks, the install command, and Codex support are recent
and marked *Proposed* in the [rules index](rules.md) until they have been
used in a real project.

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
- `bin/install`: the one command you run (once per machine, once per
  project).
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
