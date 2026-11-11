# Contributing

Partitur is a method first and code second: most changes are changes to a
rule. Issues and pull requests are welcome.

## Proposing a change to a rule

Name the rule by its ID from the [rules index](rules.md) (for example C8)
and say:

- what should change, and in which documents it is stated;
- why: the failure it prevents or the cost it removes;
- what it rests on: use in a real project (what happened, how often), or
  reasoning only.

A new rule enters as **Proposed**. It becomes **Adopted** when a project
writes it into its rules, and **Exercised** only when a record of real use
shows it working. Reports of use, including a rule that failed or was
skipped in practice, are as valuable as new rules.

## Changing code

- `project/` and `templates/` serve every project: nothing project-specific
  belongs there. A new name or format a project could want to choose goes
  through `bin/install` and [parameters](parameters.md).
- Run the tests before submitting: `python3 -m unittest discover -s tests`.
  A change to a tool comes with a test.
- One logical change per commit, with its tests and documentation.
- Each request changing user-facing behavior adds an entry at the top of
  `Unreleased` in [RELEASE-NOTES.md](RELEASE-NOTES.md): what changed and any
  action needed after updating. Use one or two lines per entry, newest first,
  with a `- ` bullet and indented continuation; keep entries independent.
  Install compares whole entries, ignoring whitespace and section moves;
  editing an entry's words makes it new again. Keep existing entries stable.
- `bin/install` must stay safe to rerun: it never overwrites or deletes,
  and it never compares a file the project owns once created.

## Release notes and local versions

Keep `Unreleased` at the top of RELEASE-NOTES.md, followed by version
sections `## v0.N (YYYY-MM-DD)`, newest first. Entries before the first
version tag stay together under `Before version tags`; earlier releases
are not assigned numbers retrospectively.

When the user decides to make a release for local use, the integration
session handles a release-notes request: change the current `Unreleased`
heading to its version and date, and add an empty `Unreleased` above it.
After review and the user's merge decision, the integration session
integrates that request into master and creates an annotated `v0.N` tag
on the resulting master commit, on the user's release decision. N starts
at 1 and counts releases used locally. The commit comes from the tag;
do not put a commit hash in its own version heading.

Install from a separate release clone at that tagged commit. Keep old
release clones while projects link to them. Moving candidate and pushing
commits or tags remain separate user decisions; only the user pushes.
Install displays tags available in its source clone and pointing directly
at the installed or source commit. It never fetches tags, uses an ancestor's
tag, or treats a lightweight tag as a release version. Commit identities
remain visible when no version tag is available.

## Style

Documents are short, plain English, wrapped at 80 columns. A rule is stated
once, where it belongs, and cited by ID elsewhere. Deliberate exceptions:
`templates/` and `project/skills/` restate rules in full, because a project
receives them without the rest of Partitur. A change to a rule therefore
also checks `templates/rules.md`, `templates/pr-README.md`, and the skills.

`rules.md` is generated from the maintainer's evidence ledger, which cites
private records of the origin project; propose changes to a rule in an
issue or pull request, and the maintainer updates the ledger and the
index.
