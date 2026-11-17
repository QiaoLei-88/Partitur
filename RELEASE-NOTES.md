# Release notes

## Unreleased

- Decisions overriding required review comments record their IDs and user reasons.
- Charters require a check of the goal itself, with a command where available.
- Reviews and done reports separate test results, model review, and approval.
- Review replies brief the plan after the decision, with details on request.
- Atomic history is complete and minimal; request skills inspect commit content.
  Clear and resume running holders after updating the rules and skills.
- README is for people; GETTING-STARTED.md shows the process by one example.
  Install and update with `install --release`, never `git pull`: INSTALL.md.
- `install --release TAG_OR_COMMIT` prepares a detached clone containing
  only the selected version and its release tags. A matching clean clone
  is reused; an incompatible existing path is refused unchanged. Clones
  default to `$XDG_DATA_HOME/partitur/releases`, or
  `~/.local/share/partitur/releases` when `XDG_DATA_HOME` is unset, empty
  or relative; `--releases-dir PATH` overrides the directory.
- Installed manifests let update and uninstall work without old Git history.
  Legacy installs migrate once; keep their source clone until migrated.
- A tag-pinned `bin/bootstrap` installs with one command, keeping the
  release clone and removing its temporary seed. See `bin/install --help`.
- Run records declare build directories in `builds:`; `test-run gc` shows
  declared and inferred groups with details. Clear and resume running holders.
- `/ptt-pr-review all` reviews one request per repository in merge order;
  others wait to rebase. Reviews across repositories complete in one run.
- Reviews and replies discuss one request per message, each with its decision.
  After updating the skills, clear and resume existing holders.
- Reports give goals, status, actions or decisions with tradeoffs. Short IDs
  omit leading zeros and pair requests with tasks.
- After updating the reporting rules and skills, clear and resume running
  holders to load them.
- Release notes use version headings backed by annotated `v0.N` tags;
  install shows those tags alongside the installed and source commits.
- Project updates print new release notes entries and required actions;
  plain install counts them, preserving the comparison until `--update`.

## Before version tags

- Codex sessions queue local inbox notices by recorded UUID (PR 29).
  Acceptance is not delivery; a closed session may receive one on resume.
- If a wrapper rejects queueing, export `PTT_CODEX_COMMAND` as one
  compatible executable path before starting Codex (PR 29).
- Queue failures keep records and give manual carry instructions (PR 29).
  Timeouts are not retried; other tools or machines still need transfer.
- Nudged sessions recheck the switch and their binding before reading
  inboxes (PR 29). Clear and resume after updating these rules and skills.
- Cancellation after a free or approved leave sends no further notice;
  the last bound session still sees it once in its inbox (PR 29).
- Take and resume repeat the recorded rename line in their final report
  when needed (PR 28); Codex always shows it. Apply that line to rename.
- Use `/ptt-brief` (Codex: `$ptt-brief`) for a briefing from this holder's
  records, including items needing your decision (PR 27).
- Reports give a short overview, then discuss one topic at a time with
  short IDs and named subjects (PR 27). Clear and resume to load the rule.
- Tasks may restrict taking to Claude Code or Codex with `tool:` (PR 26).
  Existing holders and resumes are unaffected.
- Merged task requests notify their direct supervisor (PR 26).
  The supervisor coordinates any effects on other tasks.
- Incomplete done reports offer Reopen before another report (PR 26).
  Wait is only for a task that has not reported done.
- Ended sessions receive names ending in closed, cancelled, left, or
  freed (PR 26). Apply the rename line shown to the last bound session.
- Use `/ptt-note` (Codex: `$ptt-note`) to record your message immediately
  (PR 25). A correction goes in a new note.
- Notices include manual carry instructions for unreachable sessions;
  inbox readers explain their understanding of notes first (PR 25).
- Task charters state merge order separately from take dependencies;
  reviews check that order and actual file overlap (PR 24).
- The rules index documents named resume and inbox ownership (PR 23).
  These rules remain labelled Proposed.
- Only the bound session (or a caller without a session ID) marks inbox
  items seen; unnamed resume lists holders without binding (PR 21).
- After updating these rules and skills, clear and resume running holders
  by name. Restart if new commands are not discovered by the agent tool.
