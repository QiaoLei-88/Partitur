# Partitur

[简体中文](README.zh-CN.md)

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
   record, nothing more, unless it carries out a draft you have seen.
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
| know who a session is | any | `/ptt-whoami`; `/ptt-whoami all` for everyone |
| know what is new for a session and what waits on it | any holder | `/ptt-inbox` (with an active prompt hook, it also arrives with your next message) |
| continue a role after `/clear` or in a fresh session | the continuing session | `/ptt-resume <holder name>` |
| submit finished work for review | the task holder | `/ptt-pr-submit` |
| answer a review | the task holder | `/ptt-pr-submit draft reply`, then `/ptt-pr-submit reply` (`draft` likewise before submitting) |
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
   the project's code checkouts), start a session, the *installation
   session*, and ask: "install Partitur for this project". The session runs

   ```
   ~/partitur/bin/install --scope project
   ```

   (or run it yourself inside the session, so that it sees the output: in
   Claude Code, `! ~/partitur/bin/install --scope project`) and reports
   what it created: the records repository `workspace/` with
   the rules file, task and request directories, tools and skills, the
   root design task `T0000` (the designer's charter and handover), the
   integrator's file, and the links your tools read. It lists the code
   repositories it found; one deeper down is added as a line in
   `workspace/pr/repos`. If you ran install in a plain terminal instead,
   start the installation session in the workspace root and say "Read
   partitur-install-report.md and help me finish the Partitur install":
   install leaves its output and the next steps in that file (not
   committed; delete it when done).
4. **Fill in two files** with the installation session: the "Project Rules" at the end
   of `workspace/CLAUDE.md` (your domain's rules; Partitur's own rules sit
   in a marked block above them), and the placeholders in
   `workspace/tasks/open/T0000-design/charter.md` (the root designer's
   charter, filled in directly this once and amended by you afterwards;
   its `status.md` is the designer's handover). A project that
   already has a rules file keeps it: install reports it "not merged", and
   the session compares both. It removes duplicates and keeps your domain
   rules without asking; it asks you only about real conflicts and, once,
   whether to adopt Partitur's block. On your approval `--merge-rules`
   adds the block. Then record them:

   ```
   workspace/bin/ptt record -m "install Partitur" workspace
   ```

   From now on every write in `workspace/` goes through `ptt`. Anything
   about the design agreed during the setup belongs in T0000's charter or
   `status.md` before you record. The installation session then ends; it
   takes no role.
5. **Open fresh sessions** in the workspace root for the roles: in one,
   `/ptt-take designer`; in another, `/ptt-take integrator`. Each starts
   from the records, not from the setup conversation. If T0000 is not
   filled in yet (an existing project whose handover lives elsewhere), the
   designer proposes how to fill it from what the project has. Discuss the
   first piece of work with the designer and make it a task; in a third
   session, `/ptt-take` it. Requests wait until a session holds the
   integrator role; `ptt` notes it when one is submitted without.

Always start sessions in the workspace root: Codex reads `AGENTS.md` and
skills only from the Git root of its starting directory downwards, and the
workspace root is usually not inside a Git repository.

For Codex, install also adds `.codex/hooks.json`. Review and trust the
project and its hook in Codex (`/hooks` in the CLI); until then, or on a
client without prompt hooks, use `$ptt-inbox` manually. The hook reads the
session ID from Codex's event and reports new records with the next user
message. It does not wake an idle session. See the
[official hook documentation](https://learn.chatgpt.com/docs/hooks).
The hook uses the workspace's absolute path so it also works when the
session changes directory; if the workspace moves, update that path and
review/trust the hook again.

Codex shell commands bind holders using `CODEX_THREAD_ID`, with
`CODEX_SESSION_ID` as a fallback. Claude Code continues to use
`CLAUDE_CODE_SESSION_ID`; `PTT_SESSION_ID` overrides either tool. A fresh
chat or fork continues a holder only with `$ptt-resume <holder name>`;
the previous session then loses write access through `ptt`. Continuing or
compacting the same thread does not release the holder. Run `$ptt-whoami`
to check the binding, and resume to reload the handover when needed.

To bring a project up to a newer Partitur, pull this repository and rerun
step 3's command with `--update`. The project remembers which Partitur
commit installed it (`workspace/.partitur-version`), so the update replaces
what is outdated and removes what Partitur no longer ships, but leaves your
rules, your records, and any file you changed (`--force` replaces those,
after copying each into a backup directory).
`--uninstall` removes what was installed the same way. For the user link,
`--scope user --uninstall` covers the detected tools; add `--tool all` if
you installed for both.

Both tools link `partitur` to this repository for its entry skill and
documents. Command templates in `project/skills/` are named `SKILL.md.in`;
install fills in the records directory and writes each project's `SKILL.md`.
The templates themselves are not discoverable command skills.

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
  the root design task's charter and status, the integrator's file, the
  task charter).
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
