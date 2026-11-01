# Parameters

## Chosen at install

| Choice | Option | Default |
| --- | --- | --- |
| Agent tools | `--tool auto`, `claude`, `codex`, or `all` | `auto`: the tools found on this machine |
| Project name | `--name` | the workspace root's directory name |
| Records repository | `--records` | `workspace`, directly in the workspace root |
| Its main branch | `--branch` | `master` |
| Code repositories | `--repo NAME:CHECKOUT:MAIN` (exactly these) or `--add-repo NAME:CHECKOUT:MAIN` (in addition), repeatable; later, lines in `<records>/pr/repos` | every Git checkout directly in the workspace root, with its checked-out branch |
| Backups of forced changes | `--backup-to PATH` | `<workspace root>/partitur-backup-<UTC time>/` |

Fields of the repository table are separated by whitespace and may not
contain any.

## Fixed by Partitur's tools and skills

Changing one of these means changing the tools or skills that use it.

| Name or format | Value | Rule |
| --- | --- | --- |
| Rules file | `<records>/CLAUDE.md`, Partitur's rules as a marked block, the project's outside it; linked from the workspace root as `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) | F1, F10, F13 |
| Integrator's file | `<records>/handoff/integrator.md` | D15 |
| Tasks | `<records>/tasks/{open,done,cancelled}/TNNNN[.N...]-slug/`: `charter.md`, `status.md`, events `MMMM-<kind>.md`; template `<records>/tasks/charter-template.md` | G8-G12 |
| Task IDs | `T` + four-digit number + `.N` per level + `-slug` (`T0007.2-adapter-indexing`), the directory name, never changed; short forms `T0007.2`, `0007.2`, `7.2`, the slug | G10 |
| Root design task | `<records>/tasks/open/T0000-design/`, held by the designer, supervised by the user, never closed; `designer` names it in commands | D8, G10 |
| Role records | `<records>/roles/integrator/MMMM-<kind>.md` | G1 |
| Installed version | `<records>/.partitur-version`: the Partitur commit that installed or last updated the project | F12 |
| Prompt hooks | `.claude/settings.json` (Claude Code) and `.codex/hooks.json` (Codex, trusted in Codex first) in the workspace root, each running `ptt inbox --quiet`; other settings there are kept | G17 |
| Session IDs | `PTT_SESSION_ID`, else `CLAUDE_CODE_SESSION_ID`, `CODEX_THREAD_ID`, `CODEX_SESSION_ID`; Codex's hook reads the event's `session_id` | G16 |
| Records lock | `<records>/.git/ptt.lock.d/`: names its owner (machine, process, start); removed only when the owner is known gone (`ptt unlock`) | F11 |
| Inbox markers | `<records>/.git/ptt-inbox/<holder name>`: the records commit a holder last looked at; not committed | G17 |
| Holder names | `designer-g<N>` (holders of `T0000`), `integrator-<N>`, `<kind>-<task ID>` (`track-T0007.1`), then `-2`, `-3` for later holders | G2 |
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
| Skills | `ptt-take`, `ptt-resume`, `ptt-leave`, `ptt-whoami`, `ptt-inbox`, `ptt-mktask`, `ptt-done`, `ptt-close`; `ptt-pr-submit`, `ptt-pr-draft-reply`, `ptt-pr-reply`, `ptt-pr-review`, `ptt-pr-cleanup` | G1, C1 |
| Tools | `<records>/bin/ptt` (roles and tasks), `bin/pr` (requests), `bin/test-run` | |

## Project choices with a default

Set in the rules file's "Project Rules" to differ.

| Choice | Default |
| --- | --- |
| AI attribution in commits and messages | none (C13) |
| Session names | the holder name from `/ptt-take` (G2), written in every message's `session:` field (C17) |
