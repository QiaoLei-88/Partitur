# Questions for the Codex side (temporary)

This file belongs to the branch `rules-file-and-invocation` and is deleted
before the branch is merged. Answer in the section "Answers" below, commit
on this branch, and keep each change in its own atomic commit with its
tests (`python3 -m unittest discover -s tests` passes at every commit).

## What this branch changed

1. `4ed19d5`: the rules file in the records repository is now
   `<records>/PROJECT-RULES.md` (was `<records>/CLAUDE.md`). The workspace
   root still links to it as `CLAUDE.md` (Claude Code) and `AGENTS.md`
   (Codex); no tool is meant to read it by its own name. `--update`
   renames the file of a project installed before and relinks both
   entries.
2. `44e85e1`: the eleven `ptt-*` skills that write or draft records carry
   `disable-model-invocation: true` in their frontmatter (Claude Code: the
   skill runs only when the user types `/name`, and its description stays
   out of the model's context). `partitur`, `ptt-whoami`, and `ptt-inbox`
   only read and stay invocable by the model. See `flows/authorization.md`
   and rule A12 in `templates/rules.md`.

## Questions

Label each answer Documented (cite the page), Source, Tested (cite the run:
Codex version, client, commands, result), Inferred, or Unknown.

1. **Does Codex still load the eleven skills?** Codex reads the same
   `SKILL.md` files through `.agents/skills/`. Check that the extra
   frontmatter field neither hides a skill nor produces a warning, in the
   CLI and the desktop client. This one blocks the merge.
2. **Has Codex an equivalent of `disable-model-invocation`?** A setting
   that lets a skill run only when the user invokes it (`$name`) and keeps
   its description out of the model's context, or at least stops implicit
   invocation. If it exists, implement it for the same eleven skills: where
   it lives (frontmatter, a file beside `SKILL.md`, a config), how install
   delivers it, and a test like `test_skill_frontmatter` in
   `tests/test_repo.py` that checks the split. If it does not exist, say so
   and what Codex does instead.
3. **Does the renamed rules file load in Codex?** In a project installed
   from this branch, a Codex session started in the workspace root reads
   `AGENTS.md -> <records>/PROJECT-RULES.md`. Check it once, and once after
   `--update` from a project installed at `a907d76` (the rename).

## Answers

Feedback on 2026-11-02, against `34c6f46`. This commit records findings
only; the Codex policy and the migration fix below are not implemented.

### Run and limits

**Tested.** Executable: `/usr/lib/chatgpt/resources/codex`, reporting
`codex-cli 0.166.0-alpha.5.1`. Clients: the CLI (`codex exec`) and a separate
instance of the desktop-bundled runtime (`codex app-server`). Each used
isolated temporary HOME and CODEX_HOME directories, without account
credentials. No real project or user installation was changed.

Local evidence (temporary, not included in this commit):

- Harness: `/tmp/partitur-codex-questions-probe.py`.
- Run: `/tmp/partitur-codex-questions-244isxa9/`.
- `skills-before.json`, `skills-after.json`, `fresh-thread.json`,
  `upgraded-thread.json`, `events.json`, and installation logs are in that
  run directory. CLI session JSONL files are under `implicit-before/`,
  `implicit-after/`, and `explicit-after/` there.

The harness installed this branch fresh and upgraded an installation from
`a907d76`, both with `--scope project --tool codex --records
partitur-records --name Probe --branch master` (adding `--update` for the
upgrade). It called `skills/list` with those workspace paths and
`forceReload: true`, then `thread/start` in each workspace with
`ephemeral: true`, `approvalPolicy: never`, and `sandbox: read-only`.

The CLI probes used the following command with a separate temporary
CODEX_HOME for each case; PROJECT was the workspace root, and PROMPT was
`Reply OK.` or the literal `$ptt-take`:

```sh
/usr/lib/chatgpt/resources/codex exec --json --skip-git-repo-check \
  --sandbox read-only -C "$PROJECT" \
  -c 'model_provider="probe"' -c 'model="probe"' \
  -c 'model_providers.probe.name="Local offline probe"' \
  -c 'model_providers.probe.base_url="http://127.0.0.1:9/v1"' \
  -c 'model_providers.probe.wire_api="responses"' \
  -c 'model_providers.probe.request_max_retries=0' \
  -c 'model_providers.probe.stream_max_retries=0' "$PROMPT"
```

Each CLI process was stopped at its 20-second timeout. Its session log
already contained the assembled instructions and skill context. These
checks establish context construction, not successful model responses or
execution of a Partitur command.

**Unknown.** The live desktop skill picker, its warning UI, and actual
invocation in a desktop chat have not been checked. The app-server checks
are not a substitute for that client test; question 1's desktop merge
gate remains open.

### 1. Loading the shared frontmatter

**Tested.** Both fresh and upgraded projects returned all 14 Partitur
skills from `skills/list`, all enabled, with an empty errors list. This
includes all eleven with `disable-model-invocation: true`. The CLI's
default skill catalog also contained all 14 names and descriptions.
Thus this field did not prevent discovery, but did not suppress implicit
exposure in this runtime either. No skill-loading error was reported by
the tested API; desktop warnings remain unverified.

### 2. Codex invocation policy

**Documented.** [OpenAI's skill documentation][codex-skills] specifies
`agents/openai.yaml`, relative to the skill directory:

```yaml
policy:
  allow_implicit_invocation: false
```

The documented default is true; false prevents implicit invocation while
allowing explicit `$skill` invocation.

**Tested.** Adding this file only to the eleven affected skills in the
temporary fresh installation kept all 14 discoverable and enabled in
`skills/list`. In the CLI's default skill catalog, only `partitur`,
`ptt-inbox`, and `ptt-whoami` remained from Partitur. With the literal
`$ptt-take` prompt, the session log included a separate `<skill>` message
containing the full `ptt-take` skill. Project rules still mention command
names; suppressing their catalog entries does not erase those references
or enforce a permission boundary.

**Source / proposed implementation.** Keep the Claude frontmatter. Add
the Codex policy file to the same eleven source skill directories, and
extend `project_plan` to deliver each existing policy file as a maintained
file beside the installed SKILL.md. The current loop only delivers
SKILL.md; adding source policy files alone would not install them. Both
tools already link to the same installed skill directories. Preserve
reconstruction of old commits that have no policy file. Test the exact
eleven/three split, installation, update, uninstall, and preservation of
locally modified policy files. Then repeat the runtime and desktop tests.

### 3. Renamed rules

**Tested.** In both the fresh and upgraded Codex installations,
`AGENTS.md` pointed to `partitur-records/PROJECT-RULES.md`.
`thread/start` reported the workspace's AGENTS.md in `instructionSources`.
The CLI session logs also contained the project rules body in one
instruction message. This verifies loading through the link in the
tested runtime, including the upgrade from `a907d76`.

### Additional finding: updating one tool breaks the other entry

**Tested.** Install `a907d76` with `--tool all`, then update from this
branch with `--tool codex` (same records directory). The rules file is
renamed and AGENTS.md is relinked, but the root CLAUDE.md still points to
`partitur-records/CLAUDE.md`, which no longer exists. The reproduction is
in `mixed/` and `mixed-update.log` in the run directory.

**Source.** `rename_rules` renames the shared file, while `project_plan`
only includes entry links for the tools selected in this invocation.

**Inferred / proposed fix.** During migration, also relink any existing
entry of the other tool that is demonstrably a Partitur link to the old
rules file. Do not create an uninstalled tool's entry or overwrite custom
files or links. Add regressions for both single-tool update directions
after an all-tools install, as well as preservation of custom entries.
This compatibility defect should be fixed before merging.

**Tested.** `python3 -m unittest discover -s tests` ran 100 tests:
OK, one skipped. The existing suite does not cover the mixed-tool failure
above.

[codex-skills]: https://learn.chatgpt.com/docs/build-skills#optional-metadata

## Round 2 (questions)

Since the answers above, this branch has:

- `fae3c99`: `--update` that renames the rules file also relinks the other
  tool's entry when it is Partitur's link to the old file
  (`<records>/CLAUDE.md`); any other entry is left alone. Tests:
  `test_update_for_codex_relinks_claude_entry`,
  `test_update_for_claude_relinks_codex_entry`,
  `test_update_for_one_tool_keeps_custom_entry`.
- `8748e1c`: the eleven skills carry `agents/openai.yaml` with
  `allow_implicit_invocation: false`, and install delivers it beside each
  `SKILL.md` (update, uninstall, and locally changed files as for the
  skill). Tests: `test_skill_frontmatter`,
  `test_codex_policy_files_follow_their_skills`.

Answer under "Round 2 (answers)" below, with the same labels, against the
commit you test. Change nothing else; report defects as findings.

4. **Do the installed policy files work?** Rerun your probe against this
   branch's head, with no hand-placed files: a fresh `--tool codex`
   install, and `--update` from `a907d76`. `skills/list` and the CLI's
   default skill catalog should show all 14 skills discoverable, with only
   `partitur`, `ptt-inbox`, and `ptt-whoami` in the catalog; a literal
   `$ptt-take` should still load the full `ptt-take` skill.
5. **Is the mixed-tool defect fixed?** Rerun the `mixed/` reproduction
   (install `a907d76` with `--tool all`, update with `--tool codex`), and the
   other direction (`--tool claude`): both root entries point to
   `<records>/PROJECT-RULES.md`, and Codex loads it through `AGENTS.md`.
6. **Desktop client (the open merge gate of question 1).** The user tests
   it in a new project installed from this branch. In the Codex desktop app,
   in a session started in the workspace root, check: (a) the skill picker
   and the model's skill list show no warning for the extra frontmatter or
   the policy files, and the eleven commands are not offered to the model;
   (b) typing `$ptt-take designer` runs the command (`ptt take` records the
   take; check with `$ptt-whoami`); (c) asked in plain words to take the
   designer role ("please become the designer"), the session does not
   invoke `ptt-take` by itself but tells the user to type the command.
   Record what the user observed, with the client's version.

## Round 2 (answers)

Feedback on 2026-11-02, against
`f49966b8d2bd736d41a338107790c61325293b1c`. This is a review and test report;
no implementation changes were made during the review.

### Run and limits

**Tested.** `/usr/lib/chatgpt/resources/codex` still reports
`codex-cli 0.166.0-alpha.5.1`. The clients and isolated profiles were as in
round 1: CLI context construction and a separate desktop-bundled
app-server instance, without account credentials or real project changes.

Local evidence (temporary, not included in this commit):

- Installation and app-server harness:
  `/tmp/partitur-codex-round2-probe.py`.
- CLI harness: `/tmp/partitur-codex-round2-cli.py`.
- Run directory: `/tmp/partitur-codex-round2-u_311llz/`.
- Installation logs, `skills-before.json`, four `*-thread.json` responses,
  and `events.json` record the installation and app-server checks.
- `cli-summary.json` records the four CLI assertions. Session JSONL files
  are under `fresh-implicit/`, `fresh-explicit/`, `upgraded-implicit/`, and
  `upgraded-explicit/` in that directory.

The install options, app-server methods, and CLI command were those
recorded in round 1. This time every policy file came from the installer;
none was placed or modified by hand. The CLI matrix covered both a fresh
install and an upgrade from `a907d76`, each with `Reply OK.` and the literal
`$ptt-take`. Each process reached its 20-second timeout against the
unavailable local endpoint. Assertions inspected the instructions and
skill messages already written to session logs, not model responses.

### 4. Installed policy files

**Tested.** Both fresh `--tool codex` installation and `--update` from
`a907d76` delivered exactly eleven `agents/openai.yaml` files, each with
`policy.allow_implicit_invocation: false`. For each project, `skills/list`
returned all 14 Partitur skills, enabled, with an empty errors list.

In all four CLI cases the default Partitur catalog contained exactly
`partitur`, `ptt-inbox`, and `ptt-whoami`. Both explicit cases also included
a separate `<skill>` message containing the full `ptt-take` skill; neither
implicit case did. Each case contained the project rules body in one
instruction message. The installed policies therefore produce the same
context behavior as the hand-placed policies tested in round 1.

### 5. Mixed-tool migration

**Tested.** Two separate projects were installed from `a907d76` with
`--tool all --records partitur-records`. One was updated with
`--tool codex`, the other with `--tool claude`, using the reviewed branch.
In both projects, root AGENTS.md and CLAUDE.md were valid links to
`partitur-records/PROJECT-RULES.md`. Starting an app-server thread in each
workspace reported its AGENTS.md in `instructionSources`. The original
mixed-tool failure is fixed in both directions.

**Source / Tested.** The added relinking only applies to an existing
symlink whose target is exactly the old Partitur rules path. It does not
create the other tool's absent entry or replace a custom file or link.
The regression suite checks both update directions and preservation of a
custom link. Policy delivery uses the existing maintained-file machinery;
the suite checks policy installation, addition on update, removal on
uninstall, and preservation of a locally changed policy on uninstall.

### 6. Desktop merge gate

**Unknown.** No new desktop UI observation was supplied or performed.
The skill picker, desktop warning display, a successful `ptt take`
followed by `ptt-whoami`, and the response to a plain-language request to
become the designer remain unverified. Question 6 remains an open merge
gate for the user to test with the desktop client version recorded.

**Inferred.** The policy controls default skill exposure; it does not
prevent a model from reading a skill file or running a tool through other
instructions. The natural-language check is a behavioral check of the
session and Partitur rules, not a security guarantee of the policy file.

### Review conclusion

**Tested.** `python3 -m unittest discover -s tests` ran 104 tests:
OK, one skipped (the private-terms check). `git diff --check` passed.

**Source / Inferred.** No new must-fix defect was found in the changes
since `f9d2b35`. The two implementation concerns from round 1 are resolved.
The code review passes; this does not close the desktop merge gate or
claim that a real role was taken during these probes.
