# Authorization

## Signals

| Signal | Meaning |
| --- | --- |
| (none) | Discussion. Agreement, praise, or a plan does not authorize anything *(Adopted, A1)*. |
| `AtE` | Approval to Execute: the explicit authorization for the task it is attached to (A2). |
| `AtEiYA` | AtE if you agree: form an independent view first; execute only if you agree, otherwise explain and keep discussing (A3). |
| standing AtE | Authorization for a whole scope or repository, given to one session (A8). |
| a `/ptt-*` command, or AtE naming records | The user's approval for a record (draft, release, done report, close, leave, request message): the command approves its own record and nothing more, unless it carries out a draft the user saw (`ptt-pr-submit` after its `draft`, `ptt-pr-reply` after `ptt-pr-draft-reply`); an AtE approves the records it names, several at once. Taking a role or task only by `/ptt-take` in the taking session (A12). |

## Rules

- Without authorization a session works read-only and creates no caches or
  artifacts *(Adopted, A9)*.
- After taking or resuming a role or task (`/ptt-take`, `/ptt-resume`), a
  session goes on read-only by itself: a task holder reads its charter's
  sources and amendments, inspects the code, and presents a plan ending in
  a decision list; the integrator lists requests and `pr gc`; a designer
  reports what waits on it *(Adopted, A18)*.
- An authorized task includes its necessary edits and verification; work
  outside it, or a major change within it, needs its own authorization
  *(Adopted, A5)*.
- Authorization does not travel: not from one task to the next, not
  through documents, charters, or delegation, and not from parent scope to
  child (A6, N5).
- A request states the authorization it was made under (A10).
- The commands that write or draft records are the user's to run: where
  the agent tool allows (Claude Code's `disable-model-invocation` in
  `SKILL.md`, Codex's `allow_implicit_invocation: false` in
  `agents/openai.yaml` beside it), they are not offered to the session as
  skills, and their descriptions stay out of its context; only the entry skill `partitur`, `/ptt-whoami`, and
  `/ptt-inbox`, which only read, are offered to it. Acting on an AtE that
  names records, a session follows each command's skill file
  (`<records>/skills/<command>/SKILL.md`), which has the same effect as the
  command (A12). This keeps a session from starting a command in passing
  and keeps its context free of them; it is not a permission boundary: a
  session can still read the skill file or run `ptt` itself, and only the
  rules and the user's oversight stop it, as names are not authenticated
  ([roles and tasks](tasks.md), Limits).
- Rewriting a main branch, merged commits, or the records repository needs
  its own authorization and a recovery reference first (A7).

## Asking for a decision (A13, A14, A15)

When the user must decide, the session asks with a numbered list: its
recommendation first and marked, one line per option, and always the last
option `No decision, discuss further`. The user decides with an option
number and AtE (`1 AtE`). A number without AtE, or the last option, decides
nothing: the session records and carries out nothing and continues the
discussion.

The list follows its question line directly, never another numbered list:
Markdown renders two adjacent lists as one and renumbers the second, so the
user sees other numbers than the session wrote *(Adopted, A14)*.

A number that is not an option means the user may have seen another
rendering: the session says so and asks again as the user saw it
*(Adopted, A15)*.

Two or more decisions in one message are labelled *(Adopted, A17)*: each
question gets a letter heading (A, B, ...), and its options follow it as a
bulleted list, `- A1 ...`, `- A2 ...`, recommendation first and marked, the
last `No decision, discuss further`. Bullets, not an ordered list, so
nothing renumbers them; two numbered lists numbered 1-3 in one message once
left "1 AtE" naming no question. The user answers with labels and AtE, any
subset (`A1 B2 AtE`); an unanswered question stays open and is asked again
later; a label without AtE is discussion, as a number is. A15 applies to
labels: a label that is not an option, or a bare number when labels were
shown, is said so and asked again as the user saw it.

A labelled message ends with the line "`ALL1 AtE`: accept every
recommendation" *(Adopted, A17)*. `ALL1 AtE` takes option 1, the marked
recommendation, of every question; exceptions may follow (`ALL1 B2 AtE`:
B takes 2, the rest 1). Without AtE it is discussion, as any label. A
single decision has no labels and no `ALL1` line; it is decided with
`1 AtE` as before. A15 applies: if an option 1 the user saw is not the
recommendation, the session says so and asks again as the user saw it.

```
A. Decide request 000015:
- A1 Request changes (recommended): C1, C2
- A2 Merge anyway
- A3 No decision, discuss further

B. Decide request 000016:
- B1 Merge (recommended)
- B2 No decision, discuss further

`ALL1 AtE`: accept every recommendation
```

```
Decide request 000015:
1. Request changes (recommended): C1, C2
2. Merge anyway
3. Reject
4. No decision, discuss further
```
