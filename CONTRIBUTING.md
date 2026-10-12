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
- `bin/install` must stay safe to rerun: it never overwrites or deletes,
  and it never compares a file the project owns once created.

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
