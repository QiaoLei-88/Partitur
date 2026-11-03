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
- A record (an amendment, a done report, a request message): its
  records-repository commit first, its file only as `ptt` reported it
  (`wrote tasks/open/T0007-x/0003-amend.md (records c6aa695)`) or as a
  listing shows it. Event numbers count all of a task's events, so they
  cannot be inferred; and never cite a record before it is written (D7).

## Not lasting

- Worktree paths, development branches, branch heads: removed by cleanup.
  They may appear as provenance (where something was made), never as the
  way to find it (D5).
- Review states ("waiting", "changes requested"): they change; read them
  from the request directory (D6).
- Conversations: never cited. Why: a successor cannot read them, and a
  finding told only to the user, or relayed by pasting, reaches no one else.
