"""Checks on the repository's own files.

The private-terms check reads `.private-terms` (one term per line, case
insensitive) if the file exists; it is kept out of version control, so a
public clone skips that check.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                         text=True, check=True).stdout.split()
    return [ROOT / f for f in out if (ROOT / f).is_file()]


class Repo(unittest.TestCase):
    def test_skill_frontmatter(self):
        for f in [ROOT / "SKILL.md", *sorted((ROOT / "project" / "skills").glob("*/SKILL.md"))]:
            text = f.read_text()
            self.assertTrue(text.startswith("---\n"), f)
            head = text[4:text.index("\n---\n", 4)].split("\n")
            fields = dict(line.split(": ", 1) for line in head)
            self.assertEqual(sorted(fields), ["description", "name"], f)
            self.assertEqual(fields["name"], f.parent.name if f.parent != ROOT else "partitur")
            self.assertLessEqual(len(fields["description"]), 1024, f)

    def test_record_approval_wording_agrees(self):
        """Rule A12: a command or an AtE naming the records approves them;
        taking only by /ptt-take. Every skill must say the same."""
        rules = " ".join((ROOT / "templates" / "rules.md").read_text().split())
        self.assertIn("or an AtE naming the records", rules)
        self.assertIn("Taking a role or task (`/ptt-take`) is approved only by the command", rules)
        for skill in sorted((ROOT / "project" / "skills").glob("ptt-*/SKILL.md")):
            text = " ".join(skill.read_text().split())
            if skill.parent.name == "ptt-take":
                self.assertIn("only this command, typed in the session that takes", text)
            else:
                self.assertIn("The command, or an AtE naming these records, approves", text,
                              skill.parent.name)

    def test_markdown_links_resolve(self):
        for f in tracked():
            if f.suffix != ".md":
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
