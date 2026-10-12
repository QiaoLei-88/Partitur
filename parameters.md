# Parameters

## Chosen at install

| Choice | Option | Default |
| --- | --- | --- |
| Agent tools | `--tool auto`, `claude`, `codex`, or `all` | `auto`: the tools found on this machine |
| Project name | `--name` | the workspace root's directory name |
| Records repository | `--records` | `workspace`, directly in the workspace root |
| Its main branch | `--branch` | `master` |
| Code repositories | `--repo NAME:CHECKOUT:MAIN`, repeatable; later, lines in `<records>/pr/repos` | every Git checkout directly in the workspace root, with its checked-out branch |

Fields of the repository table are separated by whitespace and may not
contain any.

## Fixed by Partitur's tools and skills

Changing one of these means changing the tools or skills that use it.

| Name or format | Value | Rule |
| --- | --- | --- |
| Rules file | `<records>/CLAUDE.md`; linked from the workspace root as `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) | F1, F10 |
| Role files | `<records>/handoff/designer.md`, `integrator.md` | D8, D15 |
| Tasks | `<records>/tasks/{open,done,cancelled}/NNNN[.N...]-slug/`: `charter.md`, `status.md`, events `MMMM-<kind>.md`; template `<records>/tasks/charter-template.md` | G8-G12 |
| Role records | `<records>/roles/{designer,integrator}/MMMM-<kind>.md` | G1 |
| Install manifest | `<records>/.partitur/manifest`: kind, SHA-256, path of every delivered file and link | F12 |
| Holder names | `designer-g<N>`, `integrator-<N>`, `<kind>-<task>`, then `-2`, `-3` for later holders | G2 |
| Stale holder | no record for 7 days, listed for the supervisor | G6 |
| Request directories | `<records>/pr/{open,merged,closed}/NNNNNN-short-name/`, six-digit numbers | C1, C3a |
| Message files | `MMMM-<kind>.md`, four digits; kinds request, review, decision, reply, cleanup | C1 |
| Worktrees | `worktrees/<topic>` in the workspace root | F2 |
| Run records | `test-runs/<UTC yyyymmddTHHMMSSZ>-<7-char sha>/` in the workspace root | E1, E7 |
| Recovery tags | `recovery/<reason>/<branch, / as ->`, then `-2`, `-3` | C8 |
| Archive tags | `archive/pr-NNNNNN` | C11 |
| Merge message | `Merge <branch> (pr NNNNNN)` | C18 |
| Cleanup cooldown | 14 days after the decision (`bin/pr gc --days N` overrides) | C11 |
| Authorization words | `AtE`, `AtEiYA` | A2, A3 |
| Skills | `ptt-take`, `ptt-leave`, `ptt-whoami`, `ptt-mktask`, `ptt-done`, `ptt-close`; `ptt-pr-submit`, `ptt-pr-review`, `ptt-pr-cleanup` | G1, C1 |
| Tools | `<records>/bin/ptt` (roles and tasks), `bin/pr` (requests), `bin/test-run` | |

## Project choices with a default

Set in the rules file's "Project Rules" to differ.

| Choice | Default |
| --- | --- |
| AI attribution in commits and messages | none (C13) |
| Session names | the holder name from `/ptt-take` (G2), written in every message's `session:` field (C17) |
