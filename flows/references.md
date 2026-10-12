# References

How records point at things so that the pointer still works after the
session, branch, and worktree are gone.

## Lasting references

- Code and documents: repository and repository-relative path, plus the
  request number before integration and the main-branch merge commit after
  it (D5).
- Records cited from code repositories: records-repository commit, request
  number, or run id; never a live path in the records repository (D7).
- Runs: run id.

## Not lasting

- Worktree paths, development branches, branch heads: removed by cleanup.
  They may appear as provenance (where something was made), never as the
  way to find it (D5).
- Review states ("waiting", "changes requested"): they change; read them
  from the request directory (D6).
- Conversations: never cited. Why: a successor cannot read them, and a
  finding told only to the user, or relayed by pasting, reaches no one else.
