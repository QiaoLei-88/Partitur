"""Tests for bin/install and the project tools (project/bin/pr, test-run),
each in a temporary directory.

Run: python3 -m unittest discover -s tests   (from the repository root)
"""
import os
import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PROJECT_BIN = HERE / "project" / "bin"
INSTALL = HERE / "bin" / "install"


def run(*args, cwd=None, check=True, env=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if check and r.returncode:
        raise AssertionError(f"{args} failed: {r.stderr}")
    return r


def git(repo, *args):
    return run("git", "-C", str(repo), *args).stdout.strip()


def message(path, **fields):
    body = "".join(f"{k}: {v}\n" for k, v in fields.items())
    path.write_text(f"---\n{body}---\n\n# text\n")


class Workspace(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.records = self.root / "records"
        (self.records / "bin").mkdir(parents=True)
        for tool in ("pr", "test-run"):
            shutil.copy(PROJECT_BIN / tool, self.records / "bin" / tool)
        self.pr = self.records / "pr"
        for state in ("open", "merged", "closed"):
            (self.pr / state).mkdir(parents=True)
        (self.pr / "repos").write_text("# name checkout main\ncode code master\n")
        self.code = self.root / "code"
        self.code.mkdir()
        git(self.code, "init", "-q", "-b", "master")
        git(self.code, "config", "user.email", "t@example.org")
        git(self.code, "config", "user.name", "t")
        (self.code / "a").write_text("a\n")
        git(self.code, "add", "a")
        git(self.code, "commit", "-qm", "base")
        self.base = git(self.code, "rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.root)

    def pr_cmd(self, *args, check=True):
        return run("python3", str(self.records / "bin" / "pr"), *args, check=check)

    def branch_commit(self, branch):
        git(self.code, "checkout", "-q", "-b", branch)
        (self.code / branch.replace("/", "-")).write_text("x\n")
        git(self.code, "add", "-A")
        git(self.code, "commit", "-qm", branch)
        head = git(self.code, "rev-parse", "HEAD")
        git(self.code, "checkout", "-q", "master")
        return head

    def request(self, state, number, branch, head, *later):
        d = self.pr / state / f"{number}-{branch.replace('/', '-')}"
        d.mkdir()
        message(d / "0001-request.md", request=number, message="0001", kind="request",
                author="requester", title=branch, repo="code", branch=branch,
                base=self.base, head=head)
        for i, fields in enumerate(later, 2):
            message(d / f"{i:04d}-{fields['kind']}.md", request=number, **fields)
        return d

    def test_list_states(self):
        h1 = self.branch_commit("docs/one")
        h2 = self.branch_commit("docs/two")
        h3 = self.branch_commit("docs/three")
        self.request("open", "000001", "docs/one", h1)
        self.request("open", "000002", "docs/two", h2,
                     dict(kind="review", author="reviewer", head=h2))
        self.request("open", "000003", "docs/three", h3,
                     dict(kind="review", author="reviewer", head=h3),
                     dict(kind="decision", author="user", head=h3,
                          decision="changes-requested"))
        out = self.pr_cmd("list").stdout
        self.assertIn("waiting for review", out)
        self.assertIn("waiting for decision", out)
        self.assertIn("waiting for author", out)
        self.assertIn("000002", self.pr_cmd("path", "pr-2").stdout)
        self.assertRegex(out, r"000001\s+open\s+code\s+-\s")

    def test_unknown_repo_flagged(self):
        h = self.branch_commit("docs/x")
        d = self.request("open", "000001", "docs/x", h)
        text = (d / "0001-request.md").read_text().replace("repo: code", "repo: other")
        (d / "0001-request.md").write_text(text)
        self.assertIn("unknown repo 'other'", self.pr_cmd("list").stdout)

    def test_missing_repo_table(self):
        h = self.branch_commit("docs/x")
        self.request("open", "000001", "docs/x", h)
        (self.pr / "repos").unlink()
        r = self.pr_cmd("list", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("repository table", r.stderr)
        self.assertIn("0001-request.md", self.pr_cmd("show", "1").stdout)

    def test_repo_table_comments_and_duplicates(self):
        (self.pr / "repos").write_text("code code master  # the code\n")
        self.assertIn("no open requests", self.pr_cmd("list").stdout)
        (self.pr / "repos").write_text("code code master\ncode other main\n")
        r = self.pr_cmd("list", check=False)
        self.assertIn("listed twice", r.stderr)

    def test_gc_missing_checkout(self):
        h = self.branch_commit("docs/x")
        self.request("closed", "000001", "docs/x", h,
                     dict(kind="decision", author="user", head=h, decision="reject",
                          date="2026-01-01"))
        (self.pr / "repos").write_text("code gone master\n")
        self.assertIn("skip: checkout gone not found", self.pr_cmd("gc", "--days", "0").stdout)

    def test_gc_merged(self):
        head = self.branch_commit("docs/one")
        git(self.code, "tag", "recovery/pre-rebase/docs-one", self.base)
        git(self.code, "tag", "recovery/pre-rebase/docs-one-2", self.base)
        git(self.code, "merge", "-q", "--no-ff", head, "-m", "Merge docs/one (pr 000001)")
        merge = git(self.code, "rev-parse", "HEAD")
        self.request("merged", "000001", "docs/one", head,
                     dict(kind="decision", author="user", head=head, decision="merge",
                          merge_commit=merge, date="2026-01-01"))
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertIn("branch -d docs/one", out)
        self.assertIn("tag -d recovery/pre-rebase/docs-one\n", out)
        self.assertIn("tag -d recovery/pre-rebase/docs-one-2\n", out)
        wait = self.pr_cmd("gc").stdout
        self.assertIn("wait:", wait)

    def test_gc_skips_moved_branch(self):
        head = self.branch_commit("docs/one")
        git(self.code, "merge", "-q", "--no-ff", head, "-m", "Merge docs/one (pr 000001)")
        merge = git(self.code, "rev-parse", "HEAD")
        self.request("merged", "000001", "docs/one", head,
                     dict(kind="decision", author="user", head=head, decision="merge",
                          merge_commit=merge, date="2026-01-01"))
        git(self.code, "checkout", "-q", "docs/one")
        (self.code / "b").write_text("b\n")
        git(self.code, "add", "b")
        git(self.code, "commit", "-qm", "later")
        git(self.code, "checkout", "-q", "master")
        self.assertIn("moved to", self.pr_cmd("gc", "--days", "0").stdout)

    def test_gc_rejected_archives(self):
        head = self.branch_commit("docs/no")
        self.request("closed", "000001", "docs/no", head,
                     dict(kind="decision", author="user", head=head, decision="reject",
                          date="2026-01-01"))
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertIn(f"tag archive/pr-000001 {head}", out)
        self.assertIn("branch -D docs/no", out)

    def test_gc_finds_merge_by_message(self):
        head = self.branch_commit("docs/one")
        git(self.code, "merge", "-q", "--no-ff", head, "-m", "Merge docs/one (pr 000001)")
        self.request("merged", "000001", "docs/one", head,
                     dict(kind="decision", author="user", head=head, decision="merge",
                          date="2026-01-01"))
        self.assertIn("branch -d docs/one", self.pr_cmd("gc", "--days", "0").stdout)

    def test_gc_rejected_without_branch_keeps_archive(self):
        head = self.branch_commit("docs/no")
        git(self.code, "tag", "recovery/pre-rebase/docs-no", head)
        git(self.code, "branch", "-D", "docs/no")
        self.request("closed", "000001", "docs/no", head,
                     dict(kind="decision", author="user", head=head, decision="reject",
                          date="2026-01-01"))
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertIn(f"tag archive/pr-000001 {head}", out)
        self.assertLess(out.index("tag archive/pr-000001"),
                        out.index("tag -d recovery/pre-rebase/docs-no"))

    def test_gc_rejected_head_missing_blocks(self):
        self.request("closed", "000001", "docs/gone", "0" * 40,
                     dict(kind="decision", author="user", head="0" * 40, decision="reject",
                          date="2026-01-01"))
        git(self.code, "tag", "recovery/pre-rebase/docs-gone", self.base)
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertIn("nothing to archive", out)
        self.assertNotIn("tag -d", out)

    def test_gc_slug_collision(self):
        h1 = self.branch_commit("a/b")
        h2 = self.branch_commit("a-b")
        for n, (b, h) in enumerate((("a/b", h1), ("a-b", h2)), 1):
            git(self.code, "merge", "-q", "--no-ff", h, "-m", f"Merge {b} (pr 00000{n})")
            self.request("merged", f"00000{n}", b, h,
                         dict(kind="decision", author="user", head=h, decision="merge",
                              date="2026-01-01"))
        git(self.code, "tag", "recovery/pre-rebase/a-b", self.base)
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertIn("branch -d a/b", out)
        self.assertIn("branch -d a-b", out)
        self.assertIn("tag -d recovery/pre-rebase/a-b", out)
        # an open request on one of the two keeps the shared tag
        h3 = self.branch_commit("a/c")
        d = self.request("open", "000003", "a-b", h3)
        out = self.pr_cmd("gc", "--days", "0").stdout
        self.assertNotIn("tag -d recovery/pre-rebase/a-b", out)

    def test_gc_worktree_removal_and_dirty_skip(self):
        head = self.branch_commit("docs/wt")
        git(self.code, "merge", "-q", "--no-ff", head, "-m", "Merge docs/wt (pr 000001)")
        wt = self.root / "worktrees" / "wt"
        git(self.code, "worktree", "add", "-q", str(wt), "docs/wt")
        self.request("merged", "000001", "docs/wt", head,
                     dict(kind="decision", author="user", head=head, decision="merge",
                          date="2026-01-01"))
        self.assertIn(f"worktree remove {wt}", self.pr_cmd("gc", "--days", "0").stdout)
        (wt / "scratch").write_text("x\n")
        self.assertIn("has changes", self.pr_cmd("gc", "--days", "0").stdout)

    def test_run_record_root_option(self):
        target = self.root / "deep" / "runs"
        out = run("python3", str(self.records / "bin" / "test-run"), "new", str(self.code),
                  "--root", str(target)).stdout.strip()
        self.assertEqual(Path(out).parent, target)

    def test_run_record(self):
        out = run("python3", str(self.records / "bin" / "test-run"), "new",
                  str(self.code)).stdout.strip()
        rec = Path(out)
        self.assertEqual(rec.parent, self.root / "test-runs")
        self.assertTrue(rec.name.endswith("-" + self.base[:7]))
        text = (rec / "run.md").read_text()
        self.assertIn(f"commit: {self.base}", text)
        self.assertIn("worktree_clean: yes", text)



class InstallProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.home = Path(tempfile.mkdtemp())
        self.env = dict(os.environ, HOME=str(self.home))
        code = self.root / "code"
        code.mkdir()
        git(code, "init", "-q", "-b", "master")

    def tearDown(self):
        shutil.rmtree(self.root)
        shutil.rmtree(self.home)

    def install(self, *extra, tool="all", check=True, cwd=None):
        where = [] if cwd else [str(self.root)]
        return run("python3", str(INSTALL), "--tool", tool, "--scope", "project",
                   *where, *extra, check=check, env=self.env, cwd=cwd)

    def test_creates_layout(self):
        out = self.install("--name", "Demo", "--records", "ws", "--repo", "code:code:master").stdout
        ws = self.root / "ws"
        self.assertEqual(git(ws, "branch", "--show-current"), "master")
        rules = (ws / "CLAUDE.md").read_text()
        self.assertIn("Demo Project Instructions", rules)
        self.assertNotIn("{{", rules)
        self.assertEqual((ws / "pr" / "repos").read_text().splitlines()[-1], "code code master")
        readme = (ws / "pr" / "README.md").read_text()
        self.assertIn("written once", readme)
        self.assertNotIn("{{", readme)
        self.assertIn("Open concerns", (ws / "handoff" / "integrator.md").read_text())
        root = ws / "tasks" / "open" / "T0000-design"
        self.assertIn("Design of Demo", (root / "charter.md").read_text())
        self.assertIn("Status of task T0000", (root / "status.md").read_text())
        ptt = [sys.executable, str(ws / "bin" / "ptt")]
        self.assertIn("T0000", run(*ptt, "tasks").stdout)
        self.assertEqual(run(*ptt, "take", "designer").stdout.strip(), "designer-g1")
        self.assertIn("Status of task T0000", (root / "status.md").read_text())
        skill = (ws / "skills" / "ptt-pr-submit" / "SKILL.md").read_text()
        self.assertNotIn("<records>", skill)
        self.assertIn("ws/pr/", skill)
        for entry, tool_dir in (("CLAUDE.md", ".claude"), ("AGENTS.md", ".agents")):
            self.assertEqual((self.root / entry).read_text(), rules)
            skills = self.root / tool_dir / "skills"
            self.assertTrue((skills / "partitur" / "SKILL.md").is_file())
            self.assertTrue((skills / "ptt-pr-review" / "SKILL.md").is_file())
        self.assertNotIn("differs", out)
        listing = run("python3", str(ws / "bin" / "pr"), "list").stdout
        self.assertIn("no open requests", listing)

    def test_one_tool_only(self):
        self.install(tool="codex")
        self.assertTrue((self.root / "AGENTS.md").is_symlink())
        self.assertTrue((self.root / ".agents" / "skills" / "ptt-pr-submit").is_symlink())
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_rerun_keeps_and_reports(self):
        self.install()
        rules = self.root / "workspace" / "CLAUDE.md"
        rules.write_text(rules.read_text() + "\nproject rule\n")
        tool = self.root / "workspace" / "bin" / "pr"
        tool.write_text(tool.read_text() + "\n# local change\n")
        out = self.install().stdout
        self.assertNotIn("created", out)
        self.assertRegex(out, r"kept\s+workspace/CLAUDE\.md")
        self.assertRegex(out, r"kept\s+workspace/pr/repos")
        self.assertRegex(out, r"(differs|modified)\s+workspace/bin/pr")
        self.assertIn("project rule", rules.read_text())
        self.assertIn("# local change", tool.read_text())

    def test_repo_options(self):
        self.install()
        table = self.root / "workspace" / "pr" / "repos"
        self.assertEqual(table.read_text().splitlines()[1:], ["code code master"])
        out = self.install("--add-repo", "lib:third/lib:main").stdout
        self.assertRegex(out, r"updated\s+workspace/pr/repos")
        self.assertEqual(table.read_text().splitlines()[1:], ["code code master",
                                                              "lib third/lib main"])
        self.assertIn("repository lib: no Git checkout at third/lib", out)
        out = self.install("--repo", "only:code:master").stdout
        self.assertRegex(out, r"replaced\s+workspace/pr/repos")
        self.assertRegex(out, r"backed up\s+workspace/pr/repos")
        self.assertEqual(table.read_text().splitlines()[1:], ["only code master"])
        req = self.root / "workspace" / "pr" / "merged" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text("---\nrepo: research\n---\n")
        out = self.install().stdout
        self.assertIn("requests name repository research", out)
        self.assertIn("--add-repo research:<checkout>:<main branch>", out)

    def test_rules_merge_into_existing_file(self):
        ws = self.root / "workspace"
        ws.mkdir()
        git(ws, "init", "-q", "-b", "master")
        (ws / "pr").mkdir()
        rules = ws / "CLAUDE.md"
        rules.write_text("# My project\n\nOur own rules.\n\n## Domain\n\n- keep units SI\n")
        out = self.install().stdout
        self.assertRegex(out, r"not merged\s+workspace/CLAUDE.md")
        self.assertIn("contradiction", out)
        self.assertNotIn("partitur rules begin", rules.read_text())
        out = self.install("--merge-rules").stdout
        self.assertRegex(out, r"merged\s+workspace/CLAUDE.md")
        text = rules.read_text()
        self.assertTrue(text.startswith("# My project\n\nOur own rules.\n\n<!-- partitur rules begin"))
        self.assertIn("- keep units SI", text)
        self.assertRegex(self.install().stdout, r"kept\s+workspace/CLAUDE.md")

    def partitur_clone(self):
        """A committed copy of Partitur, to install from and then change."""
        clone = self.home / "partitur"
        shutil.copytree(HERE, clone, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        for args in (["init", "-q", "-b", "master"], ["add", "-A"],
                     ["-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "v1"]):
            git(clone, *args)
        return clone

    def commit_clone(self, clone, message):
        git(clone, "add", "-A")
        git(clone, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", message)

    def install_from(self, clone, *extra, check=True):
        return run("python3", str(clone / "bin" / "install"), "--tool", "claude", "--scope",
                   "project", str(self.root), *extra, check=check, env=self.env)

    def test_update_from_designer_role_layout(self):
        """A project installed when the designer was a role (handoff/designer.md)
        updates without error and is told where that file's content goes."""
        clone = self.partitur_clone()
        templates = clone / "templates"
        (templates / "designer.md").write_text("# Designer of {{PROJECT}}\n")
        charter, status = (templates / n for n in ("root-charter.md", "root-status.md"))
        saved = charter.read_text(), status.read_text()
        charter.unlink()
        status.unlink()
        self.commit_clone(clone, "designer as a role")
        self.install_from(clone)
        ws = self.root / "workspace"
        self.assertTrue((ws / "handoff" / "designer.md").exists())
        self.assertFalse((ws / "tasks" / "open" / "T0000-design").exists())
        (templates / "designer.md").unlink()
        charter.write_text(saved[0])
        status.write_text(saved[1])
        self.commit_clone(clone, "root design task")
        for extra in ((), ("--update",)):
            out = self.install_from(clone, *extra).stdout
            self.assertRegex(out, r"superseded\s+workspace/handoff/designer.md")
            self.assertIn("T0000-design/charter.md", out)
        self.assertTrue((ws / "handoff" / "designer.md").exists())
        self.assertTrue((ws / "tasks" / "open" / "T0000-design" / "charter.md").exists())
        self.assertNotIn("superseded", self.install_from(clone).stdout)
        self.install_from(clone, "--uninstall")

    def test_update_replaces_outdated_keeps_modified(self):
        clone = self.partitur_clone()
        out = self.install_from(clone).stdout
        stamp = (self.root / "workspace" / ".partitur-version").read_text()
        self.assertIn(git(clone, "rev-parse", "HEAD"), stamp)
        self.assertNotIn("uncommitted", out)
        ws = self.root / "workspace"
        mine = ws / "bin" / "test-run"
        mine.write_text(mine.read_text() + "\n# my change\n")
        rules = ws / "CLAUDE.md"
        rules.write_text(rules.read_text() + "\nproject rule\n")
        for name in ("pr", "test-run"):
            f = clone / "project" / "bin" / name
            f.write_text(f.read_text() + "\n# v2\n")
        self.commit_clone(clone, "v2")
        out = self.install_from(clone).stdout
        self.assertRegex(out, r"outdated\s+workspace/bin/pr")
        self.assertRegex(out, r"modified\s+workspace/bin/test-run")
        self.assertIn("--update", out)
        out = self.install_from(clone, "--update").stdout
        self.assertRegex(out, r"updated\s+workspace/bin/pr")
        self.assertIn("# v2", (ws / "bin" / "pr").read_text())
        self.assertIn("# my change", mine.read_text())
        self.assertIn("project rule", rules.read_text())
        self.assertIn(git(clone, "rev-parse", "HEAD"),
                      (ws / ".partitur-version").read_text())
        out = self.install_from(clone, "--update", "--force").stdout
        self.assertRegex(out, r"replaced\s+workspace/bin/test-run")
        self.assertNotIn("# my change", mine.read_text())

    def test_update_removes_what_is_no_longer_shipped(self):
        clone = self.partitur_clone()
        self.install_from(clone)
        old = self.root / "workspace" / "skills" / "ptt-whoami"
        self.assertTrue((self.root / ".claude" / "skills" / "ptt-whoami").is_symlink())
        shutil.move(clone / "project" / "skills" / "ptt-whoami",
                    clone / "project" / "skills" / "ptt-who")
        self.commit_clone(clone, "rename a skill")
        out = self.install_from(clone).stdout
        self.assertRegex(out, r"obsolete\s+workspace/skills/ptt-whoami/SKILL.md")
        self.assertRegex(out, r"created\s+workspace/skills/ptt-who/SKILL.md")
        self.assertTrue(old.exists())
        out = self.install_from(clone, "--update").stdout
        self.assertRegex(out, r"removed\s+workspace/skills/ptt-whoami/SKILL.md")
        self.assertRegex(out, r"removed\s+\.claude/skills/ptt-whoami")
        self.assertFalse(old.exists())
        self.assertFalse((self.root / ".claude" / "skills" / "ptt-whoami").is_symlink())

    def test_rules_block_update_and_forced_backup(self):
        clone = self.partitur_clone()
        self.install_from(clone)
        rules = self.root / "workspace" / "CLAUDE.md"
        rules.write_text(rules.read_text().replace("(Rules specific to this project.)",
                                                   "- our domain rule"))
        t = clone / "templates" / "rules.md"
        t.write_text(t.read_text().replace("## Authorization and Scope",
                                           "## Authorization and Scope\n\n- a v2 rule"))
        tool = clone / "project" / "bin" / "pr"
        tool.write_text(tool.read_text() + "\n# v2\n")
        self.commit_clone(clone, "v2")
        mine = self.root / "workspace" / "bin" / "pr"
        mine.write_text(mine.read_text() + "\n# mine\n")
        out = self.install_from(clone).stdout
        self.assertRegex(out, r"outdated\s+workspace/CLAUDE.md")
        out = self.install_from(clone, "--update").stdout
        self.assertRegex(out, r"updated\s+workspace/CLAUDE.md")
        text = rules.read_text()
        self.assertIn("- a v2 rule", text)
        self.assertIn("- our domain rule", text)
        backups = self.home / "bk"
        out = self.install_from(clone, "--update", "--force", "--backup-to", str(backups)).stdout
        self.assertRegex(out, r"replaced\s+workspace/bin/pr")
        self.assertIn("# mine", (backups / "workspace" / "bin" / "pr").read_text())
        self.assertNotIn("# mine", mine.read_text())
        self.assertIn(f"Backups of replaced or removed files: {backups}", out)
        out = self.install_from(clone, "--uninstall").stdout
        self.assertRegex(out, r"removed\s+workspace/CLAUDE.md")
        self.assertNotIn("partitur rules begin", rules.read_text())
        self.assertIn("- our domain rule", rules.read_text())

    def test_uninstall_keeps_records_and_changes(self):
        clone = self.partitur_clone()
        self.install_from(clone)
        ws = self.root / "workspace"
        task = ws / "tasks" / "open" / "0001-x"
        task.mkdir()
        (task / "charter.md").write_text("a task\n")
        mine = ws / "bin" / "pr"
        mine.write_text(mine.read_text() + "\n# mine\n")
        out = self.install_from(clone, "--uninstall").stdout
        self.assertRegex(out, r"removed\s+workspace/bin/ptt")
        self.assertRegex(out, r"removed\s+CLAUDE\.md")
        self.assertRegex(out, r"modified\s+workspace/bin/pr")
        self.assertFalse((ws / "bin" / "ptt").exists())
        self.assertFalse((self.root / "CLAUDE.md").is_symlink())
        self.assertFalse((self.root / ".claude").exists())
        self.assertTrue((ws / "CLAUDE.md").exists())
        self.assertTrue((task / "charter.md").exists())
        self.assertTrue(mine.exists())
        self.assertFalse((ws / ".partitur-version").exists())

    def test_uninstall_without_stamp(self):
        r = self.install("--uninstall", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nothing to uninstall", r.stderr)

    def test_defaults_detect_checkouts(self):
        other = self.root / "lib"
        other.mkdir()
        git(other, "init", "-q", "-b", "main")
        out = self.install(tool="claude", cwd=self.root).stdout
        self.assertIn("found      code (main branch master)", out)
        self.assertNotIn("warning  code", out)
        table = (self.root / "workspace" / "pr" / "repos").read_text().splitlines()
        self.assertEqual(table[1:], ["code code master", "lib lib main"])
        self.assertIn(f"{self.root.name} Project Instructions",
                      (self.root / "workspace" / "CLAUDE.md").read_text())
        again = self.install(tool="claude", cwd=self.root).stdout
        self.assertNotIn("found", again)

    def test_installed_skills_match_partitur(self):
        self.install()
        for skill in [p.name for p in (HERE / "project" / "skills").iterdir()]:
            src = (HERE / "project" / "skills" / skill / "SKILL.md").read_text()
            got = (self.root / "workspace" / "skills" / skill / "SKILL.md").read_text()
            self.assertEqual(got, src.replace("<records>", "workspace"))
        self.assertIn("https://github.com/", (self.root / "workspace" / "CLAUDE.md").read_text())
        self.assertNotIn(str(HERE), (self.root / "workspace" / "CLAUDE.md").read_text())

    def test_existing_entry_file_warns(self):
        (self.root / "CLAUDE.md").write_text("old notes\n")
        out = self.install(tool="claude").stdout
        self.assertRegex(out, r"warning\s+CLAUDE\.md\ exists\ and\ is\ not\ the\ rules\ file")
        self.assertEqual((self.root / "CLAUDE.md").read_text(), "old notes\n")

    def test_unusual_main_branch_warns(self):
        dev = self.root / "dev"
        dev.mkdir()
        git(dev, "init", "-q", "-b", "develop")
        out = self.install(tool="claude").stdout
        self.assertRegex(out, r"warning\s+dev:\ is\ develop\ its\ main\ branch\?")

    def test_refuses_code_repository_as_records(self):
        code = self.root / "code"
        (code / "f").write_text("x\n")
        git(code, "add", "f")
        git(code, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "x")
        r = self.install("--records", "code", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((code / "pr").exists())

    def test_user_scope_link_not_duplicated(self):
        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.home / ".claude" / "skills" / "partitur").symlink_to(HERE)
        out = self.install().stdout
        self.assertRegex(out, r"skipped\s+\.claude/skills/partitur")
        self.assertFalse((self.root / ".claude" / "skills" / "partitur").exists())
        self.assertTrue((self.root / ".agents" / "skills" / "partitur").is_symlink())

    def test_bad_arguments(self):
        for extra in (["--repo", "code:code"], ["--repo", "c:my code:main"],
                      ["--records", "a/b"]):
            r = self.install(*extra, check=False)
            self.assertNotEqual(r.returncode, 0, extra)
        self.assertFalse((self.root / "workspace").exists())

    def test_missing_scope_changes_nothing(self):
        r = run("python3", str(INSTALL), str(self.root), check=False, env=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--scope user", r.stdout)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["code"])

    def test_auto_detects_tools(self):
        tools = self.home / "bin"
        tools.mkdir()
        for name in ("git", "python3"):
            (tools / name).symlink_to(shutil.which(name))
        env = dict(self.env, PATH=str(tools))
        r = run(str(tools / "python3"), str(INSTALL), "--scope", "project", str(self.root),
                check=False, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("found neither", r.stderr)
        (self.home / ".codex").mkdir()
        out = run(str(tools / "python3"), str(INSTALL), "--scope", "project", str(self.root),
                  env=env).stdout
        self.assertIn("detected Codex", out)
        self.assertTrue((self.root / "AGENTS.md").is_symlink())
        self.assertFalse((self.root / "CLAUDE.md").exists())


class InstallUser(unittest.TestCase):
    def test_links_per_tool_and_reruns(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ, HOME=str(home))
        try:
            out = run("python3", str(INSTALL), "--tool", "codex", "--scope", "user",
                      env=env).stdout
            self.assertIn("created", out)
            self.assertTrue((home / ".agents" / "skills" / "partitur" / "SKILL.md").is_file())
            self.assertFalse((home / ".claude").exists())
            out = run("python3", str(INSTALL), "--tool", "all", "--scope", "user",
                      env=env).stdout
            self.assertRegex(out, r"kept\s+\.agents/skills/partitur")
            self.assertRegex(out, r"created\s+\.claude/skills/partitur")
            (home / ".claude" / "skills" / "partitur").unlink()
            (home / ".claude" / "skills" / "partitur").mkdir()
            out = run("python3", str(INSTALL), "--tool", "claude", "--scope", "user",
                      env=env).stdout
            self.assertRegex(out, r"differs\s+\.claude/skills/partitur")
            (home / ".claude" / "skills" / "partitur").rmdir()
            run("python3", str(INSTALL), "--tool", "all", "--scope", "user", env=env)
            out = run("python3", str(INSTALL), "--tool", "all", "--scope", "user",
                      "--uninstall", env=env).stdout
            self.assertRegex(out, r"removed\s+\.agents/skills/partitur")
            self.assertFalse((home / ".claude" / "skills" / "partitur").is_symlink())
        finally:
            shutil.rmtree(home)


if __name__ == "__main__":
    unittest.main()
