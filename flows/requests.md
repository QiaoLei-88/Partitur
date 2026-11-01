# Requests

How a change reaches a main branch. The procedures are the request skills
(submit, draft-reply and reply, review, cleanup); this file is the protocol
they implement.

## Layout

```
pr/
  repos               the repository table
  open/               waiting for review, decision, or changes
  merged/             merged into their repository's main branch
  closed/             rejected or withdrawn
    NNNNNN-short-name/  one request, in whichever of the three it is
      0001-request.md   requester: summary, repo, branch, base, head, worktree
      0002-review.md    integrator: analysis, comments C1..., recommendation
      0003-decision.md  user's decision, recorded by the integrator
      0004-reply.md     requester: answers by comment ID, new head
      ...
      MMMM-cleanup.md   integrator: what was removed after the cooldown
```

One request system serves several repositories; each request names its
repository, and a table maps repositories to checkouts and main branches
(C12).

## Rules

1. **Write once.** A message is written by one session and not edited
   afterwards (C1). The one standing exception is renumbering after a
   collision (C3b). Any other correction is a one-off that needs the user's
   authorization and states its reason in the commit.
2. **State is derived.** Directory plus latest message give the state; a
   read-only helper reports it (C2). Status sections never copy it (D6).
3. **Numbers.** Request numbers by atomic `mkdir` *(Adopted, C3a)*; message
   numbers one above the highest present, checked again just before
   committing, and the later writer renumbers on a collision (C3b). Why:
   requester and reviewer do write the same number at the same moment.
4. **Pinned heads.** Every message names the head it refers to; a review of
   a moved branch is stale (C4).
5. **Review recommends.** The integrator's review ends in a recommendation;
   the user decides; the decision is a message of its own, quoting the user
   (C5, C16).
6. **Requester moves freely.** Replies and updates may come at any time;
   decisions gate only merging and closing (C7).
7. **Comments by ID**, continued across rounds, each marked required or
   optional; replies answer every ID (C6).
8. **Rewrites.** Rebase and fixup are routine on the request's branch. Tag
   the old head `recovery/<reason>/<branch-slug>` (`-2`, `-3` when
   repeated) before rewriting; the reply gives old-to-new SHAs and a
   `range-diff` summary (C8). Why: a rewritten head is otherwise unreachable,
   and the review that read it can no longer be checked.
9. **History quality.** Atomic commits are a review criterion; the aim is
   one logical change per commit, not fewer commits (C9).
10. **Merge.** `--no-ff`, only after the main branch is checked again to be
    an ancestor of the head, with the message `Merge <branch> (pr NNNNNN)`;
    the request directory is then moved and recorded in one step
    (`ptt pr-move`) (C10, C18, F11).
11. **Cleanup** after a cooldown: worktrees, branches, recovery tags;
    rejected heads kept as `archive/pr-NNNNNN` (C11).
12. **Withdrawal**: the user may withdraw a request; the integrator records
    it as a decision and moves the request to `closed/` *(Proposed, C19)*.
13. **No AI attribution** in commits, merges, or messages, unless the
    project chooses otherwise (C13; [parameters](../parameters.md)).

## Turns

| Latest message | Whose turn |
| --- | --- |
| request, reply | integrator: review |
| review | user: decide |
| decision recorded, not yet carried out | integrator: merge or move the directory |
| decision: changes requested | requester: reply |
| decision: merged, rejected, or withdrawn | integrator: cleanup after the cooldown (C11) |
| cleanup | nobody: the request is finished |
