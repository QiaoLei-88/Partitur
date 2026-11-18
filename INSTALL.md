# Installing Partitur

This file is for the agent session that installs, updates, or removes
Partitur for a project. People need not read it: they ask a session, and
the session reads this. A session working in a project already installed
reads [SKILL.md](SKILL.md) instead.

Command examples use Claude Code's `/ptt-*` notation; in Codex invoke the
same skills as `$ptt-*`.

## Before you start

- Requirements: Git 2.28 or later, Python 3.8 or later, symbolic links
  (Linux or macOS; on Windows, WSL); Claude Code, Codex, or both.
- Work from the project's *workspace root*: the directory that holds its
  code checkouts. Sessions always start there: Codex reads `AGENTS.md` and
  skills only from the Git root of its starting directory downwards, and
  the workspace root is usually not inside a Git repository.
- The user's request to install is the AtE for installing. Locations and
  the version are the user's to confirm: say them and wait for the
  go-ahead before you clone or run anything.

## Release clones

A project installs from a *release clone*: a clone of Partitur holding
one version only, checked out detached at its commit, kept in a lasting
place, and named by that commit. The project links to it by absolute
path, so never `git pull` it or switch it to another branch or commit:
every project linked to it would change at once. A newer version is a
new release clone next to the old one.

The version is an annotated tag `v0.N` when there is one, otherwise a
commit; name it by tag or commit, never "latest". Unless the user names
one, propose the newest tag (`git ls-remote --tags` on
https://github.com/QiaoLei-88/Partitur), or the head of the repository's
default branch when it has no tag (it holds only versions its author
uses).

Never make or check a release clone by hand: `install --release
TAG_OR_COMMIT` does it, then runs that version's installer with the
other options. It guarantees:

- The clone is `partitur-<first seven hex digits of the commit>` in the
  releases directory: `$XDG_DATA_HOME/partitur/releases`, or
  `~/.local/share/partitur/releases` when `XDG_DATA_HOME` is unset, empty
  or relative; `--releases-dir PATH` chooses another (ask the user).
- A tag must be an annotated `v0.N` tag. A version that is not found
  stops install and creates nothing; it never falls back to another
  version.
- An existing clone is reused only if it is clean, detached, at that
  commit, and holds only that version and its release tags; otherwise
  install stops and leaves it untouched. A new clone that fails these
  checks is removed.

`--release` resolves the version in the clone it runs from, which holds
only its own version, so a new version starts from a temporary seed. In
the steps below, `<release> OPTIONS` stands for one of these two
commands, run from the workspace root:

- For a tag, the bootstrap pinned to that tag: download it, read it
  before running it, then run and remove it:

  ```
  f=$(mktemp)
  curl -fsSL -o "$f" https://raw.githubusercontent.com/QiaoLei-88/Partitur/<tag>/bin/bootstrap
  sh "$f" <tag> OPTIONS
  rm "$f"
  ```

  It fetches only that tag into a temporary seed, runs `install --release
  <tag> OPTIONS` there, and removes the seed; the release clone stays.
- For a commit, a seed cloned from the default branch:

  ```
  seed=$(mktemp -d)
  git clone -q https://github.com/QiaoLei-88/Partitur "$seed"
  "$seed"/bin/install --release <commit> OPTIONS
  rm -rf "$seed"
  ```

## Installing for a project

1. Tell the user the version, the releases directory, and the command
   below; wait for the go-ahead.
2. From the workspace root:

   ```
   <release> --scope project
   ```

   It detects the agent tools on this machine and installs for those; if
   the project should serve a tool not installed here, add `--tool all`
   (ask the user). The tools are recorded in `<records>/.partitur-version`;
   later runs (install, `--update`, `--uninstall`) follow them on any
   machine, and `--tool` adds one (with `--uninstall`, removes only that
   one). The command is in use (F9, F10); report anything unexpected.
   Everything else has a default (see [parameters](parameters.md));
   `--repo` is needed only for checkouts not directly in the workspace
   root, which can also be added later as lines in `<records>/pr/repos`.
   `bin/install` without arguments, in a release clone, prints every
   option.
3. Report the output to the user, including anything reported as
   differing. Install also writes `partitur-install-report.md` in the
   workspace root: its output and the next steps below as they apply to
   this run. When the user ran install in a terminal and asks you to finish
   it ("Read partitur-install-report.md and help me finish the Partitur
   install"), read that file and work through its steps; delete it, with
   the user's approval, when they are done.

What install creates: the records repository (`workspace/` unless
`--records` names another) with the rules file `PROJECT-RULES.md`, task
and request directories, the tools `ptt`, `pr`, and `test-run`, the
`ptt-*` skills, the root design task `T0000` (the designer's charter and
handover), and the integrator's file; in the workspace root, the links
each tool reads (`CLAUDE.md` and `.claude/skills/` for Claude Code,
`AGENTS.md` and `.agents/skills/` for Codex) and a prompt hook that shows
each session what is new for it. Command templates in `project/skills/`
are named `SKILL.md.in`; install fills in the records directory and
writes each project's `SKILL.md`. The templates themselves are not
discoverable command skills.

Then, with the user:

1. **Rules.** If install reports the rules file "not merged" (an existing
   project with its own rules), read the project's rules and Partitur's
   rules block (`templates/rules.md`, between the markers). Installing
   Partitur already chose its rules, so ask the user only where the project
   deliberately differs. Sort each of the project's rules into one of four
   kinds:
   - **Duplicate** of a rule in the block: it is removed; list what you
     remove, do not ask.
   - **Domain rule**, or a concrete instance of a general rule in the block
     (the project's names, paths, repositories, conventions): it stays,
     unchanged, under "## Project Rules"; do not ask.
   - **Conflict**, where the project's rule says otherwise than the block:
     ask, one question per conflict, as a numbered list right after its
     question line (`1. Partitur's rule`, `2. Keep the project's rule as a
     stated deviation`, `3. No decision, discuss further`), your
     recommendation first (usually the block's rule); with several
     conflicts in one message, label them (`A1`, `B2`) and end with the
     `ALL1 AtE` line; see the decision
     list in [authorization](flows/authorization.md). If the user keeps the
     project's way, it goes under "## Project Rules" as a stated deviation
     ("Partitur's rule on ... does not apply here: ..."), because install
     maintains the block and it is never edited.
   - **Partitur's rules the project lacks** come with the block. Ask one
     question for all of them: adopt the block. Name the rules not yet
     exercised in practice *(Proposed, T1)*: a successor checking its
     handover against the records; withdrawing a request; offering to be
     cleared at quiet points; and of the task rules, refusing to leave while
     something waits, freeing a silent holder, sub-design scopes, and
     checking holders before naming them (G5-G7, G10, G14, G15, G18). The
     user drops one only by saying so, as a stated deviation.

   Present the conflicts and the one block question together. On the
   user's approval, run install again with `--merge-rules` and write the
   project's part after the block as you sorted it. A new project gets the
   block at install; fill in its "Project Rules": domain rules, and any
   choice that differs from the defaults (T2).
2. **Repositories.** If install warns that requests name a repository the
   table lacks, or a checkout lies deeper than the workspace root, propose
   the `--add-repo NAME:CHECKOUT:MAIN` line and run it when the user agrees.
3. **Root design task.** Fill in `<records>/tasks/open/T0000-design/charter.md`,
   the root designer's charter, with the user (this first fill-in is a
   direct edit; later changes are the user's amendments). If the project
   has its own design handover, the user may leave this to the designer,
   who proposes it on taking T0000. Anything about the design agreed during
   the setup goes into T0000's charter or `status.md`.
4. **Superseded files.** If install reports a file "superseded", move its
   content as the note says, with the user's approval, delete it.
5. **Record and end.** Record the records repository:
   `<records>/bin/ptt record -m "install Partitur" <records>`. From now on
   every write in the records repository goes through `ptt`. You are the
   installation session: you take no role. Tell the user to open fresh
   sessions in the workspace root for the roles (`/ptt-take designer`,
   `/ptt-take integrator`), which start from the records, and that requests
   wait until a session holds the integrator role.
6. **User link (optional).** If the report offers linking Partitur for the
   user, ask once; on the user's approval run the command it names, then
   this install again with `--update`, which removes the project's own
   link.

## Hooks and session binding

Claude Code: install adds a prompt hook to `.claude/settings.json` that
runs `ptt inbox --quiet` and prints only when the records hold something
new for the session's holder; other settings there are kept.

Codex: install adds `.codex/hooks.json`. The user reviews and trusts the
project and its hook in Codex (`/hooks` in the CLI); explain this step from
the install report. Until then, or on a client without prompt hooks, use
`$ptt-inbox` manually. The hook reads the session ID from Codex's event and
reports new records with the next user message; it does not wake an idle
session. See the [official hook
documentation](https://learn.chatgpt.com/docs/hooks). The hook uses the
workspace's absolute path so it also works when the session changes
directory; if the workspace moves, update that path and review and trust
the hook again.

Sessions bind to holders by session ID: Claude Code's
`CLAUDE_CODE_SESSION_ID`; in Codex `CODEX_THREAD_ID`, with
`CODEX_SESSION_ID` as a fallback; `PTT_SESSION_ID` overrides either tool.
A fresh session, chat, or fork continues a holder only with `/ptt-resume
<holder name>`; the previous session then loses write access through
`ptt`. Continuing or compacting the same session does not release the
holder. `/ptt-whoami` shows the binding.

## Updating

1. Tell the user the new version and the command below; never pull the
   old clone.
2. From the workspace root, with the user's go-ahead:

   ```
   <release> --scope project --update
   ```

   The project's stamp (`<records>/.partitur-version`) says which commit
   and clone installed it, and for which tools. The update replaces what is
   outdated, removes what Partitur no longer ships, and moves the
   `partitur` skill links to the new clone, but leaves the rules outside
   the block, the records, and any file the project changed (`--force`
   replaces those after copying each into a backup directory; ask the user
   first).
3. The update prints the new [release notes](RELEASE-NOTES.md) entries and
   the actions they require, such as clearing and resuming running
   holders: pass them to the user. Plain install only counts the entries
   and keeps the comparison until `--update`. An older commit without
   release notes gives a reading pointer; an unknown commit shows the
   `Unreleased` section with a note that the difference is unknown.
   Installed and source commits show their `v0.N` tags when the source
   clone has them; the commit remains their identity.
4. Record: `<records>/bin/ptt record -m "update Partitur to <tag or
   commit>" <records>`.

Keep the old release clone while any project links to it: another
project's stamp names its clone in its `source` line. A project installed
before installed manifests also needs it for its first update, which
recovers the manifest once from the installing commit in that clone.
Remove an old clone only with the user's approval.

## User scope

```
<release> --scope user
```

links the release clone as the skill `partitur` for every session of
this user (`~/.claude/skills/partitur`, `~/.agents/skills/partitur`), so
that a session in any directory can install Partitur by being asked. It
is one link per tool and keeps no stamp. Run from a newer clone, it
keeps an existing link to an older one and says so; to move it, run
`<linked-clone>/bin/install --scope user --uninstall` (it removes every
`partitur` link to a Partitur clone, or only those `--tool` names), then
`<release> --scope user` at the new version. After adding the user link,
a project's `--update` removes the project's own `partitur` link, so
that Codex does not list the skill twice.

## Uninstalling

```
<clone>/bin/install --scope project --uninstall
```

removes every maintained file and link still as delivered; it keeps the
rules file, the charters and other seeded files, files changed here, and
every record (tasks, requests, roles). `--tool` removes only that tool's
links and hook while another tool remains; `--force` also removes files
changed here, after backing each up. Run it from the clone the stamp
names (its `source` line): `<clone>` here is that clone. It removes what
the installed manifest (`<records>/.partitur-manifest.json`) records; a
project installed before manifests recovers that record once from its
installing commit, which that clone holds. Ask
the user before using `--force` or deleting the records repository, which
install never does.
