"""Checks on the repository's own files.

The private-terms check reads `.private-terms` (one term per line, case
insensitive) if the file exists; it is kept out of version control, so a
public clone skips that check.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A calling Git (rebase --exec, a hook) exports variables such as GIT_DIR that
# would point the tests' git commands at its repository instead of theirs.
for _var in subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True,
                           text=True, check=True).stdout.split():
    os.environ.pop(_var, None)


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                         text=True, check=True).stdout.split()
    return [ROOT / f for f in out if (ROOT / f).is_file()]


class Repo(unittest.TestCase):
    def test_tests_ignore_a_calling_gits_repository(self):
        # git rebase --exec and hooks export GIT_DIR; the tests' own git
        # commands must still reach only their temporary repositories
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            caller = Path(d) / ".git"
            def snapshot():
                return {p.relative_to(caller): p.read_bytes()
                        for p in caller.rglob("*") if p.is_file()}
            before = snapshot()
            env = dict(os.environ, GIT_DIR=str(caller), GIT_WORK_TREE=d)
            r = subprocess.run([sys.executable, "-m", "unittest", "test_ptt.Ptt.test_task_lifecycle",
                                "test_tools.Workspace.test_list_states"], cwd=ROOT / "tests", env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(snapshot(), before)

    def test_skill_frontmatter(self):
        for f in [ROOT / "SKILL.md", *sorted((ROOT / "project" / "skills").glob("*/SKILL.md.in"))]:
            text = f.read_text()
            self.assertTrue(text.startswith("---\n"), f)
            head = text[4:text.index("\n---\n", 4)].split("\n")
            fields = dict(line.split(": ", 1) for line in head)
            # the commands that write or draft records are the user's to run (A12)
            explicit = f.parent.name not in ("ptt-inbox", "ptt-whoami") and f.parent != ROOT
            self.assertEqual(sorted(fields), ["description", *(["disable-model-invocation"]
                                                              if explicit else []), "name"], f)
            if explicit:
                self.assertEqual(fields["disable-model-invocation"], "true", f)
            # and Codex's equivalent beside it, for the same commands
            policy = f.parent / "agents" / "openai.yaml"
            self.assertEqual(policy.read_text() if policy.exists() else None,
                             "policy:\n  allow_implicit_invocation: false\n" if explicit else None,
                             f)
            self.assertEqual(fields["name"], f.parent.name if f.parent != ROOT else "partitur")
            description = fields["description"]
            if description.startswith('"'):
                description = json.loads(description)
            else:
                self.assertNotIn(": ", description, f"{f}: quote YAML descriptions with colons")
            self.assertLessEqual(len(description), 1024, f)

    def test_record_approval_wording_agrees(self):
        """Rule A12: a command or an AtE naming the records approves them;
        taking only by /ptt-take. Every skill must say the same."""
        rules = " ".join((ROOT / "templates" / "rules.md").read_text().split())
        self.assertIn("or an AtE naming the records", rules)
        self.assertIn("Taking a role or task (`/ptt-take`) is approved only by the command", rules)
        for skill in sorted((ROOT / "project" / "skills").glob("ptt-*/SKILL.md.in")):
            text = " ".join(skill.read_text().split())
            if skill.parent.name == "ptt-take":
                self.assertIn("only this command, typed in the session that takes", text)
            else:
                self.assertIn("The command, or an AtE naming these records, approves", text,
                              skill.parent.name)

    def test_note_is_user_invoked_and_recipient_explains_its_understanding(self):
        skills = ROOT / "project/skills"
        note = " ".join((skills / "ptt-note/SKILL.md.in").read_text().split())
        self.assertIn("the work it proposes still needs AtE", note)
        self.assertIn("Show no draft or approval question first", note)
        self.assertIn("no summary of the note", note)
        self.assertIn("A correction goes in a new note", note)
        inbox = " ".join((skills / "ptt-inbox/SKILL.md.in").read_text().split())
        self.assertIn("first state in one or two sentences your understanding", inbox)
        self.assertIn("then what that means for your work", inbox)

    def test_user_direction_overrides_cleanup_limits(self):
        """T0010: ownership and head rules limit only what a session proposes
        by itself; what the user names, any session cleans up."""
        disk = " ".join((ROOT / "project" / "skills" / "ptt-disk" / "SKILL.md.in").read_text().split())
        self.assertIn("when the user names run records or a scratchpad to clean up, do it", disk)
        evidence = " ".join((ROOT / "flows" / "evidence.md").read_text().split())
        self.assertIn("when the user names run records or a scratchpad to clean up, any session does it",
                      evidence)
        for name in ("ptt-done", "ptt-leave", "ptt-pr-review", "ptt-pr-cleanup"):
            text = (ROOT / "project" / "skills" / name / "SKILL.md.in").read_text()
            self.assertIn("ptt-disk", text, name)
        # T0010 amendment 0008: the rules block says the same as the skills.
        rules = " ".join((ROOT / "templates" / "rules.md").read_text().split())
        self.assertIn("`test-run new` records the run's creator (`by:`)", rules)
        self.assertIn("a run nobody cites may go whole and a cited one keeps all but its declared and inferred build directories", rules)
        self.assertIn("`builds:` accepts one path or a block list of paths relative to the run directory", rules)
        self.assertIn("a session inspects its own inferred directories before proposing them", rules)
        self.assertIn("as static removal commands run only on the user's AtE", rules)
        self.assertIn("Run records or a scratchpad the user names, any session removes.", rules)
        self.assertIn("a task's: `worktrees/<task slug>`", rules)
        self.assertIn("`by:`", evidence)
        self.assertIn("worktrees/<task slug>", evidence)
        self.assertIn("Run all listed commands", disk)
        self.assertIn("inspect each inferred directory of your own runs", disk)
        self.assertIn("Run only declared build-directory commands", disk)

    def test_read_only_start_after_take_and_resume(self):
        """T0010 amendment 0004: after a take or resume, a session goes on
        read-only by itself; the rules block, the flow, and both skills agree."""
        def text(*parts):
            return " ".join(ROOT.joinpath(*parts).read_text().split())
        rules = text("templates", "rules.md")
        self.assertIn("After taking or resuming a role or task, a session goes on read-only by itself", rules)
        self.assertIn("goes on read-only by itself", text("flows", "authorization.md"))
        take = text("project", "skills", "ptt-take", "SKILL.md.in")
        for phrase in ("Then go on by yourself, read-only (rules file)",
                       "wait for AtE", "end with a decision list asking for AtE",
                       "`<records>/bin/pr gc`", "list what waits on it"):
            self.assertIn(phrase, take)
        resume = text("project", "skills", "ptt-resume", "SKILL.md.in")
        self.assertIn("Then go on read-only as after a take", resume)
        self.assertIn("what remains, from `status.md`", resume)

    def test_take_and_resume_repeat_rename_in_the_final_report(self):
        """T0021 amendment 0003: keep the reminder, after the overview."""
        def text(name):
            return " ".join((ROOT / "project/skills" / name / "SKILL.md.in").read_text().split())
        take = text("ptt-take")
        resume = text("ptt-resume")
        for wording in (take, resume):
            for phrase in ("final report (plan or decision list)", "`/rename <name>`",
                           "recorded session name", "the business items",
                           "first action: in this session (`<tool>`)"):
                self.assertIn(phrase, wording)
        for phrase in ('`ListAgents` ("This session is ...")',
                       "omit the reminder when they match",
                       "In Codex the current name cannot be read, so always list the reminder after the overview",
                       "Introduce any decision options with their own question line"):
            self.assertIn(phrase, take)
        self.assertIn("After the overview in the final report", take)
        self.assertIn("apply the rename check in `/ptt-take`, step 4", resume)
        self.assertIn("give the rename reminder after the overview", resume)

    def test_rules_name_commands_in_the_sessions_tool(self):
        rules = " ".join((ROOT / "templates" / "rules.md").read_text().split())
        self.assertIn("Name a command for the user in your own tool's notation.", rules)

    def test_merge_order_is_stated_amended_and_reviewed(self):
        """T0013: charter order reaches review without becoming a take dependency."""
        def text(*parts):
            return " ".join(ROOT.joinpath(*parts).read_text().split())
        charter = text("templates", "charter.md")
        for phrase in ("## Merge order", "after: <task or request>", "reason:",
                       "cleared when:", "Independent of other open tasks.",
                       "`depends:` instead gates taking"):
            self.assertIn(phrase, charter)
        draft = text("project", "skills", "ptt-mktask", "SKILL.md.in")
        for phrase in ("Independent of other open tasks.", "Sub-designers",
                       "amends the waiting task", "its `after:` decides",
                       "`before:` in the other charter is only a pointer",
                       "no extra note to the holder", "already has a request submitted",
                       "`to: integrator`", "A merged request cannot be reordered"):
            self.assertIn(phrase, draft)
        review = text("project", "skills", "ptt-pr-review", "SKILL.md.in")
        for phrase in ("`Merge order` and all amendments", "pr list all", "pr show",
                       "actual file overlap", "<prerequisite merge commit> <head>",
                       "conflicting charter orders", "unforeseen overlap", "`to: designer`",
                       "the integrator does not change the order",
                       "A charter without the section is \"not stated\"",
                       "mergeable as to order", "reason still holding",
                       "Merge order: <mergeable as to order"):
            self.assertIn(phrase, review)
        for path in (("templates", "rules.md"), ("flows", "tasks.md")):
            wording = text(*path)
            self.assertIn("waiting task", wording)
            self.assertIn("`depends:` gates taking", wording)
        for path in (("templates", "rules.md"), ("flows", "requests.md")):
            self.assertIn("records the finding in the review", text(*path))
        self.assertIn("merge order with reasons and clearing conditions",
                      text("flows", "handoff.md"))

    def test_decision_list_wording_agrees(self):
        """Rule A13: the options follow their question line, never another
        numbered list; a number that is not an option is asked again."""
        def text(*parts):
            return " ".join(ROOT.joinpath(*parts).read_text().split())
        rules = text("templates", "rules.md")
        self.assertIn("right after its question line, never after another numbered list", rules)
        self.assertIn("A number that is not an option means the user may have seen another rendering", rules)
        flow = text("flows", "authorization.md")
        self.assertIn("The list follows its question line directly, never another numbered list", flow)
        self.assertIn("A number that is not an option means the user may have seen another rendering", flow)
        self.assertIn("right after its question line", text("INSTALL.md"))
        self.assertIn("decision list right after its question line", text("project", "skills", "ptt-close", "SKILL.md.in"))
        review = text("project", "skills", "ptt-pr-review", "SKILL.md.in")
        self.assertIn("decision list right after its question line, never after another numbered list", review)
        self.assertIn("one that is not an option: ask again", review)
        self.assertIn("an option number, a label, or `ALL1` with AtE", review)
        # T0010 amendment 0011: ALL1 takes every recommendation; not for one decision.
        self.assertIn("\"`ALL1 AtE`: accept every recommendation\"", rules)
        self.assertIn("(`ALL1 B2 AtE`: B takes 2, the rest 1)", rules)
        self.assertIn("A single decision has no labels and no `ALL1` line", rules)
        self.assertIn("A single decision has no labels and no `ALL1` line", flow)
        self.assertIn("`ALL1 AtE`: accept every recommendation ```", flow)
        for name in ("ptt-close", "ptt-pr-cleanup", "ptt-pr-reply", "ptt-pr-review"):
            self.assertIn("ALL1 AtE", text("project", "skills", name, "SKILL.md.in"), name)
        self.assertIn("`ALL1 AtE` line", text("INSTALL.md"))
        # T0017: labelled decisions stay within one topic.
        self.assertIn("Two or more decisions of one topic in one message are labelled", rules)
        self.assertIn("(`A1 B2 AtE`)", rules)
        self.assertIn("a bare number when labels were shown", rules)
        self.assertIn("Two or more decisions of one topic in one message are labelled", flow)
        self.assertIn("- A1 Request changes", flow)
        for name in ("ptt-close", "ptt-pr-cleanup", "ptt-pr-reply", "ptt-pr-review"):
            self.assertIn("rules file", text("project", "skills", name, "SKILL.md.in"))
            self.assertIn("A1", text("project", "skills", name, "SKILL.md.in"), name)
        self.assertIn("label them (`A1`, `B2`)", text("INSTALL.md"))

    def test_review_all_selects_one_request_per_repository_before_decisions(self):
        """T0020: batch the reviews across repositories, not the decisions."""
        review = " ".join((ROOT / "project/skills/ptt-pr-review/SKILL.md.in").read_text().split())
        for phrase in ('group requests "waiting for review" by repository',
                       "`Merge order` and amendments", "before selecting",
                       "select only the first request in that order",
                       "lowest request number when no order is stated",
                       "leave that repository waiting until its order is resolved",
                       "continue with independent repositories",
                       "`waits: rebase after PR N merges`; do not review it",
                       "for every selected request in the same run, before asking for any decision",
                       "overview line per request, reviewed or waiting",
                       "a later `all` selects again from the current states and merge order"):
            self.assertIn(phrase, review)
        self.assertNotIn('Review every request "waiting for review", lowest first', review)
        flow = " ".join((ROOT / "flows/requests.md").read_text().split())
        for phrase in ("first request per repository in merge order",
                       "lowest request number when no order is stated",
                       "`waits: rebase after PR N merges`",
                       "Finish recording the selected reviews before asking for decisions"):
            self.assertIn(phrase, flow)
        for name, selection, reply in (
                ("README.md", "first waiting request per repository",
                 "`/ptt-pr-reply` likewise handles one request per message"),
                ("README.zh-CN.md", "按合并顺序选取每个仓库的首个待审请求",
                 "`/ptt-pr-reply` 同样每条消息只处理一个请求")):
            wording = " ".join((ROOT / name).read_text().split())
            self.assertIn("`/ptt-pr-review all`", wording, name)
            self.assertIn(selection, wording, name)
            self.assertIn(reply, wording, name)

    def test_request_decisions_stay_in_separate_messages(self):
        for name in ("ptt-pr-review", "ptt-pr-reply"):
            wording = " ".join((ROOT / "project/skills" / name / "SKILL.md.in").read_text().split())
            for phrase in ("one request per message",
                           "Use a numbered decision list for one decision",
                           "For several decisions on that request, label each question",
                           "decisions about different requests in separate messages"):
                self.assertIn(phrase, wording, name)
        for skill in (ROOT / "project/skills").glob("*/SKILL.md.in"):
            wording = " ".join(skill.read_text().split())
            self.assertNotIn("For several requests in one message", wording, skill)
            self.assertNotIn("With `all`, or any other decision in the same message", wording, skill)

    def test_close_reopens_an_incomplete_done_report(self):
        text = " ".join((ROOT / "project/skills/ptt-close/SKILL.md.in").read_text().split())
        self.assertIn("`1. Reopen` (the missing criteria) / `2. No decision, discuss further`", text)
        self.assertNotIn("`2. Wait`", text)
        self.assertIn('ptt reopen <N> --as <name> --reason "<missing criteria>"', text)
        self.assertIn("Wait only when no done report exists", text)

    def test_reports_take_one_topic_at_a_time(self):
        """T0021 amendment 0003: preserve the full agreed reporting rule."""
        rules = " ".join((ROOT / "templates/rules.md").read_text().split())
        expected = " ".join("""
            - Report to the user one topic at a time, concise and to the point:
              cut words, never parts. Read a change before reporting it. Start
              with an overview: one line per topic, about 20 to 30 Chinese
              characters or 15 English words, saying what happened and who acts
              next (`PR 24 merged into master; T13 to send its done report`),
              never only that something changed; mark the topic now taken up.
              Then take up that topic alone: its goal in one line; where it
              stands; and the user's part, one of three:
              - None: say why, and who drives the work now.
              - An action: where, and the exact text ready to paste (in session
                `<name>` (`<tool>`) type `<command>`; in a terminal in
                `<directory>` run `<command>`); without such text, the steps
                and what to check. Do yourself what the tools let you.
              - A decision: first its conflict, two sides (X against Y), wording
                or behaviour, apart from the background; then the options that
                resolve it, each with its cost and gain, as its own decision
                list. The next topic follows the user's answer.

              Use short IDs without leading zeros (`PR 24`, `T13`), name a
              request with its task (`PR 29 (T18)`), and name every subject;
              no pronoun without a clear antecedent.
        """.split())
        self.assertIn(expected + " - When the user must decide,", rules)
        for name in ("ptt-take", "ptt-resume", "ptt-inbox"):
            text = " ".join((ROOT / "project/skills" / name / "SKILL.md.in").read_text().split())
            self.assertIn("Report as the rules file says: an overview line per item, "
                          "then one topic at a time.", text, name)

    def test_brief_reads_the_holders_scope_before_reporting(self):
        """T0017 amendment 0002: a user-only briefing, without new records."""
        text = " ".join((ROOT / "project/skills/ptt-brief/SKILL.md.in").read_text().split())
        for phrase in ("`<records>/bin/ptt whoami`", "If no holder is bound here",
                       "`<records>/bin/ptt who`", "`<records>/bin/pr list`",
                       "`<records>/bin/ptt inbox`", "Designer:", "Integrator:",
                       "Task holder:", "Read the status records and notes",
                       "`<records>/bin/pr show N`", "pr list all",
                       "Mark missing or unread evidence Unknown",
                       "never report a change you have not read",
                       "overview line per item, then one topic at a time",
                       "Mark the items waiting on the user",
                       "first item waiting on the user alone",
                       "giving the action or decision as the rules file says",
                       "If no item needs the user, say why and who drives the work now",
                       "write no status, note, review, decision, or other record",
                       "do not carry out the reported next steps"):
            self.assertIn(phrase, text)

    def test_atomic_history_is_defined_once_and_checked_by_content(self):
        def text(*parts):
            return " ".join(ROOT.joinpath(*parts).read_text().split())
        rules = text("templates", "rules.md")
        expected = " ".join("""
            Commits are atomic: each commit is one logical change, complete and
            minimal. Complete: everything the change needs is in the commit,
            including its tests and documentation, and nothing of it lies in
            another commit. Minimal: the commit holds no other change that
            stands on its own, even one serving the same feature (for example, a
            refactoring the feature needs is its own commit, before the
            feature). A request's history records these changes, not how the
            work went. A commit that breaks completeness is folded into the
            commit it belongs to; such commits include, but are not limited to:
            a fixup, work in progress, a revert, a later commit changing what an
            earlier commit of the same branch introduced, and a document entry
            added per step instead of one entry for the result. A commit that
            breaks minimality is split. When in doubt, keep commits separate:
            folding them later is easier than splitting one. Check the content
            of the commits, not only the files they touch (`git log -p
            <main>..HEAD`). Inspect status, staged changes, and whitespace before
            committing.
        """.split())
        self.assertEqual(rules.split("- Commits are atomic: ")[1].split(" - ")[0],
                         expected.removeprefix("Commits are atomic: "))
        submit = text("project", "skills", "ptt-pr-submit", "SKILL.md.in")
        self.assertIn("and its history atomic (rules file; `git log -p <main>..HEAD`)", submit)
        reply = text("project", "skills", "ptt-pr-reply", "SKILL.md.in")
        self.assertIn("Code changes go on the same branch: a change to an existing commit "
                      "of the branch is folded into that commit, and only a new logical "
                      "change is a new commit (rules file, atomic commits); the branch "
                      "is checked as for submitting", reply)
        review = text("project", "skills", "ptt-pr-review", "SKILL.md.in")
        expected_review = " ".join("""
            and the history (`git log -p <base>..<head>`), against
            atomicity (rules file). The author keeps commits separate when in
            doubt; the review settles that doubt. For each commit ask: is it
            complete, or does a later commit of the branch change what it
            introduced, or does it need something that lies in another commit?
            Is it minimal, or does it hold a change that stands on its own? For
            each pair of neighbouring commits ask whether they are one change.
            Each message says what its commit changes. A history that breaks
            atomicity gets a required comment naming the commits and the result
            intended (fold with fixup/autosquash, or split); that means
            recommending changes. Commits the review finds no reason to fold
            stay separate. A claim that each commit builds and passes on its own
            needs a run of each commit.
        """.split())
        self.assertIn(expected_review, review)
        for wording in (submit, reply, review):
            self.assertNotIn("git log --stat", wording)
            self.assertNotIn("fold fixups, drop WIP", wording)
            self.assertNotIn("Messy history (", wording)

    def test_reply_is_drafted_and_released_by_its_own_commands(self):
        """Replies to a review: /ptt-pr-draft-reply writes nothing, /ptt-pr-reply
        releases; /ptt-pr-submit no longer replies."""
        skills = ROOT / "project" / "skills"
        def text(name):
            return " ".join((skills / name / "SKILL.md.in").read_text().split())
        self.assertNotIn("draft reply", text("ptt-pr-submit"))
        self.assertNotIn("`reply [N]`", text("ptt-pr-submit"))
        self.assertIn("Write nothing", text("ptt-pr-draft-reply"))
        self.assertIn("/ptt-pr-reply", text("ptt-pr-draft-reply"))
        self.assertIn("No draft for request NNNNNN in this conversation", text("ptt-pr-reply"))
        self.assertIn("kind: reply", text("ptt-pr-reply"))

    def test_markdown_links_resolve(self):
        for f in tracked():
            if not f.name.endswith((".md", ".md.in")):
                continue
            for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", f.read_text()):
                if not target.startswith(("http://", "https://")):
                    self.assertTrue((f.parent / target).exists(), f"{f}: {target}")

    def test_cited_rule_ids_exist(self):
        index = (ROOT / "rules.md").read_text()
        known = set(re.findall(r"^\| ([A-Z]\d+[a-z]?) \|", index, re.M))
        self.assertGreater(len(known), 50)
        docs = [ROOT / "model.md", ROOT / "SKILL.md", ROOT / "INSTALL.md", ROOT / "CONTRIBUTING.md",
                *ROOT.glob("roles/*.md"), *ROOT.glob("flows/*.md")]
        for f in docs:
            for cited in re.findall(r"\b([A-GNT]\d{1,2}[ab]?)\b", f.read_text()):
                self.assertIn(cited, known, f"{f.relative_to(ROOT)} cites {cited}")

    def test_no_private_terms(self):
        terms_file = ROOT / ".private-terms"
        if not terms_file.exists():
            self.skipTest("no .private-terms file")
        terms = [t.strip().lower() for t in terms_file.read_text().splitlines() if t.strip()]
        for f in tracked():
            try:
                text = f.read_text().lower()
            except UnicodeDecodeError:
                continue
            for t in terms:
                self.assertNotIn(t, text, f"{f.relative_to(ROOT)} contains a private term")


if __name__ == "__main__":
    unittest.main()
