# Model

The concepts of Partitur and the invariants that hold for every project
using it. Rules are cited by their ID in [the rules index](rules.md), which
holds their labels. An unmarked rule is in use in practice;
*(Adopted)* marks a rule written into a project's rules but not yet shown in
use, *(Proposed)* one that is neither.

## Concepts

- **Authority.** The user. The only source of authorization (A2, N5), and
  the decider of every merge and rejection (B1, C5) and of every design
  decision labelled Agreed (D10). Choices below the level the user works at
  are made by the session itself and recorded with reasons *(Proposed,
  A11)*.
- **Session.** One run of an AI agent. Disposable: it may end at any time,
  and nothing it alone remembers survives it (B7). It holds a role or a
  task only by taking it (`/ptt-take`), which records it and gives it a
  holder name *(Proposed, G1, G2)*.
- **Role.** A contract a session holds: what it decides, what it may write,
  what it hands on. Roles are stable; sessions holding them change. The
  [user](roles/user.md) and the [integrator](roles/integrator.md) serve the
  whole project; the [designer](roles/designer.md), [track](roles/track.md),
  and [worker](roles/worker.md) work in one scope; a
  [delegate](roles/delegate.md) belongs to the session that started it.
- **Scope.** A part of the project with its own charter: the whole project
  at the root, a sub-area or a single task below. Scopes form a tree
  ([nesting](#scopes-and-nesting)).
- **Record.** A file under version control, or a run record outside it.
  Records are the only memory the project has (D12).
- **Records repository.** The repository holding the rules file, tasks, role
  records and files, and requests, beside the code repositories; each agent
  tool's entry point links to its rules file instead of copying it (F1).
  Sessions commit to it directly, each only the paths it owns (C14), all
  through `ptt record` under one lock *(Proposed, F11)*; it has no
  requests of its own.
- **Code repository.** A repository the project delivers into, with one
  **main branch** that changes only by merges of decided requests (C5,
  F2).
- **Design document.** The designer's record of decisions, labelled Agreed,
  Proposed, or Open, in a code repository (for example `docs/design.md`),
  so that it changes only through requests like any other code (D14).
- **Knowledge repository.** A repository of research notes kept by tracks
  and shared across sessions, often packaged as a skill (F5).
- **Task and charter.** A task is one piece of work a session can take: a
  directory under `tasks/` with the designer's *charter* (what to do, what
  to read, where results go, what is out of scope, when it is done; D1),
  the holder's `status.md` (D2), and its events (release, take, leave,
  done, close) *(Proposed, G8-G12)*. A `design` task opens a sub-scope.
  The root design task `T0000` is the root designer's: chartered by the
  user, never closed, its `status.md` the handover from one designer to the
  next (D8). A task's ID is `T`, its number, and its slug
  (`T0007.2-adapter-indexing`), also its directory name, and never changes.
  See [roles and tasks](flows/tasks.md).
- **Request.** A proposed change to a main branch, reviewed and decided as
  a directory of numbered messages ([requests](flows/requests.md)).
- **Run record.** The evidence of one verification run, written once
  ([evidence](flows/evidence.md)).
- **Parameters.** What a project chooses at install, and the names and
  formats Partitur fixes: [parameters](parameters.md).

## Invariants

1. **Nothing happens without authorization.** Discussion is the default
   *(Adopted, A1)*; work starts with the user's AtE for that task, or with
   AtEiYA after the session agrees (A2, A3). Records never expand
   authorization (A6), and authority does not nest (N5).
2. **One writer per file.** Every record names its owner; others propose,
   the owner writes (B8, C14).
3. **Records over memory.** A fact that matters beyond the current session
   goes into a record, located by a lasting reference (D5, D12).
4. **Pointers over copies.** State that lives in one place is not restated
   elsewhere; a request's state is read from its directory, never stored in
   a status record (C2, D6).
5. **Review recommends, the user decides.** Nothing enters a main branch
   without a recorded decision of the user (C5).
6. **Claims carry their evidence.** Decisions are labelled Agreed, Proposed,
   or Open; evidence Documented, Source, Inferred, Tested, or Unknown
   (D10). A cited result has a record (E4).
7. **History is not rewritten silently.** Branches under review may be
   rebased with a recovery tag and a mapping; main branches and records only
   with separate authorization (A7, C8).

## Scopes and nesting

A *design scope* has one designer. A task opens either a child design
scope (kind `design`), held by a *sub-designer* (the principal of a
section), or a leaf: a track or a worker. The root designer holds the root
design task `T0000`, chartered by the user; every sub-designer holds a
design task chartered by its parent designer. Task numbers show the tree:
`T0007` is a top-level task in the root scope, `T0007.1` a task in the
scope of design task `T0007`. The *level* of a design scope is the number
of parts of its task number (`T0007` level 1, `T0007.1` level 2), and the
root `T0000` is level 0; its
*generation* counts the sessions that have taken it (`designer-g2`,
`design-T0007-2`) *(Proposed, G10)*.

- Ownership is a tree: the parent owns a child task's charter except its status
  section; the child owns its own records (N2).
- A decision is made in the lowest scope that contains all its effects; one
  that touches a sibling or the charter's interface goes up to the common
  parent, which decides it with the user (N3).
- Findings flow up as files (N4). A sub-designer reports each decision it
  records with the user in its status record at once, so that the parent
  can raise a conflict with the user before it spreads *(Proposed, N9)*.
- The user authorizes every session directly, at every depth; a designer
  never authorizes on the user's behalf (N5).
- One integrator serves the whole tree; requests name their scope
  *(Proposed, N7)*.
- Each designer has its own handover file and closes its own stages
  *(Proposed at depth > 1, N6)*. A sub-designer is chartered only when a
  scope has design decisions of its own and more than one track
  *(Proposed, N8)*.

A project starts as one design scope with leaf tasks. It grows a level
only when a scope needs one.

## Starting small

The smallest setup is two sessions: one that works and an integrator that
reviews its requests, because no session reviews its own work (C5). In it,
one session may take the root design task (the designer) and then the tasks
it made, under a holder name for each, as long as every change still reaches
a main branch through a request; closing its own task is then checked by the
user *(Proposed, N10)*. Separate sessions are added when the work grows
apart.

## Information flow

```
               user (authority)
         AtE ↓   ↑ reports, questions; notices between sessions
             designer ──  tasks   ──► tracks, workers, sub-designers
                ▲                          │
                └─ status.md, notes ───────┘
  designers, tracks, workers ── requests ──► integrator ── review ──► user
                                     ◄── decision, recorded ──
```

Findings travel as records; the user carries the notice that something is
there (D12). Sessions do not message each other *(Proposed otherwise,
D12b)*.
