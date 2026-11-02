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

(Codex side: write here.)
