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

    def test_rules_name_commands_in_the_sessions_tool(self):
        rules = " ".join((ROOT / "templates" / "rules.md").read_text().split())
        self.assertIn("Name a command for the user in your own tool's notation.", rules)

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
        self.assertIn("right after its question line", text("SKILL.md"))
        self.assertIn("decision list right after its question line", text("project", "skills", "ptt-close", "SKILL.md.in"))
        review = text("project", "skills", "ptt-pr-review", "SKILL.md.in")
        self.assertIn("decision list right after its question line, never after another numbered list", review)
        self.assertIn("a number that is not an option: ask again", review)

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
        docs = [ROOT / "model.md", ROOT / "SKILL.md", ROOT / "CONTRIBUTING.md",
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
