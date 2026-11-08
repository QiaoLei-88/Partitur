# Evidence

## Labels

Two axes (D10):

- **Decisions:** Agreed (the user agreed), Proposed, Open.
- **Evidence:** Source (read in the source), Inferred (follows, not
  checked), Tested (run and observed), Unknown, and Documented (stated by
  the source's documentation) *(Adopted)*.

A claim without a label is a claim the reader cannot weigh.

## Run records

- One directory per run, `test-runs/<UTC timestamp>-<short sha>`, created by
  a tool that records the checkout's identity and the holder that made it
  (`by:`); written once, never reused, cited by id (E1).
- Holds commands, environment, identifiers, exit status, counts, logs, and a
  report (E6). Small files in full; large outputs by hash, size, and a
  numerical summary, compared by tolerance (E2).
- Lifetime *(Adopted, E9)*: a run lives while the development head it tested
  is open (a request not decided, a task open, or, without a request, its
  worktree still present). A run without a request belongs to the task
  whose worktree it ran in, `worktrees/<task slug>` by convention
  ([tasks](tasks.md)). Once the head is concluded (the request merged,
  rejected, or withdrawn; the task closed or cancelled), a run nobody cites
  may go whole, and a cited one keeps everything but its build directories.
  Cited means its id is in a records file, a records commit message, or a
  main-branch commit message. There is no cooldown. `bin/test-run gc` lists
  this, read-only, with static removal commands for the caller's own runs
  (`by:`); runs on a main branch or with no head stay until someone names
  them. The user's direction is not limited by this: when the user names
  run records or a scratchpad to clean up, any session does it.
- Outside every repository (E7). A one-off probe's driver is kept in the
  run record with its outputs; a reusable driver belongs in the code
  repository's tests *(Adopted)* (E8).

## Rules

- A cited result needs a record; a computation nobody recorded is not
  evidence (E4). Why: a figure that cannot be traced back to a run cannot be
  rechecked when it is questioned, and it will be questioned.
- Skipped, unrun, or unfinished work is stated as such, never counted as a
  pass (E5).
- Unit tests live with the code and are permanent; fixed cases and expected
  results in their own repository; output becomes expected only by a
  deliberate commit (E3a, E3b).
