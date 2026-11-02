"""Tests for bin/install and the project tools (project/bin/pr, test-run),
each in a temporary directory.

Run: python3 -m unittest discover -s tests   (from the repository root)
"""
import json
import os
import re
import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PROJECT_BIN = HERE / "project" / "bin"
INSTALL = HERE / "bin" / "install"
N_SKILLS = len([d for d in (HERE / "project" / "skills").iterdir() if d.is_dir()])


def run(*args, cwd=None, check=True, env=None):
    if env is None:
        env = dict(os.environ)
        for key in ("PTT_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID",
                    "CODEX_SESSION_ID"):
            env.pop(key, None)
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if check and r.returncode:
        raise AssertionError(f"{args} failed: {r.stderr}")
    return r


def git(repo, *args):
    return run("git", "-C", str(repo), *args).stdout.strip()


def skill_files(root):
    """Include nested skills reached through directory symlinks."""
    return [Path(directory) / "SKILL.md"
            for directory, _, files in os.walk(root, followlinks=True)
            if "SKILL.md" in files]


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
        for key in ("PTT_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID",
                    "CODEX_SESSION_ID"):
            self.env.pop(key, None)
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
        rules = (ws / "PROJECT-RULES.md").read_text()
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
        report = (self.root / "partitur-install-report.md").read_text()
        self.assertIn("fill in `ws/tasks/open/T0000-design/charter.md`", report)
        self.assertIn("it takes no role", report)
        self.assertIn('ptt record -m "install Partitur" ws', report)
        self.assertNotIn("partitur-install-report", git(ws, "status", "--porcelain"))
        listing = run("python3", str(ws / "bin" / "pr"), "list").stdout
        self.assertIn("no open requests", listing)

    def test_one_tool_only(self):
        self.install(tool="codex")
        self.assertTrue((self.root / "AGENTS.md").is_symlink())
        self.assertTrue((self.root / ".agents" / "skills" / "ptt-pr-submit").is_symlink())
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_both_tools_discover_only_installed_skills(self):
        self.install("--records", "partitur-records", tool="all")
        skills = self.root / ".agents" / "skills"
        expected = ["partitur", *[p.name for p in (HERE / "project/skills").iterdir()]]
        for directory in (".agents", ".claude"):
            found = skill_files(self.root / directory / "skills")
            self.assertEqual(sorted(p.parent.name for p in found), sorted(expected))
            for path in found:
                if path.parent.name.startswith("ptt-"):
                    self.assertNotIn("<records>", path.read_text())
                    self.assertIn("partitur-records/bin/", path.read_text())
        entry = skills / "partitur"
        for directory, _, files in os.walk(entry, followlinks=True):
            for name in files:
                path = Path(directory) / name
                if path.suffix == ".md":
                    for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", path.read_text()):
                        if not target.startswith(("http://", "https://")):
                            self.assertTrue((path.parent / target).exists(), (path, target))
        self.assertEqual((entry / "bin/install").resolve(), INSTALL)
        self.assertEqual(entry.resolve(), HERE)
        self.assertEqual((self.root / ".claude/skills/partitur").resolve(), HERE)
        self.assertNotIn("created", self.install("--records", "partitur-records").stdout)

    def test_rerun_keeps_and_reports(self):
        self.install()
        rules = self.root / "workspace" / "PROJECT-RULES.md"
        rules.write_text(rules.read_text() + "\nproject rule\n")
        tool = self.root / "workspace" / "bin" / "pr"
        tool.write_text(tool.read_text() + "\n# local change\n")
        out = self.install().stdout
        self.assertNotIn("created", out)
        self.assertRegex(out, r"kept\s+workspace/PROJECT-RULES\.md")
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
        rules = ws / "PROJECT-RULES.md"
        rules.write_text("# My project\n\nOur own rules.\n\n## Domain\n\n- keep units SI\n")
        out = self.install().stdout
        self.assertRegex(out, r"not merged\s+workspace/PROJECT-RULES.md")
        self.assertIn("real conflicts", out)
        self.assertNotIn("partitur rules begin", rules.read_text())
        report = (self.root / "partitur-install-report.md").read_text()
        self.assertIn("rerun this install with --merge-rules", report)
        self.assertIn("not merged", report)                 # the output, kept
        self.assertIn("Read partitur-install-report.md", out)
        out = self.install("--merge-rules").stdout
        self.assertRegex(out, r"merged\s+workspace/PROJECT-RULES.md")
        text = rules.read_text()
        self.assertTrue(text.startswith("# My project\n\nOur own rules.\n\n<!-- partitur rules begin"))
        self.assertIn("- keep units SI", text)
        self.assertRegex(self.install().stdout, r"kept\s+workspace/PROJECT-RULES.md")

    def partitur_clone(self, name="partitur"):
        """A committed copy of Partitur, to install from and then change."""
        clone = self.home / name
        shutil.copytree(HERE, clone, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__"))
        for args in (["init", "-q", "-b", "master"], ["add", "-A"],
                     ["-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "v1"]):
            git(clone, *args)
        return clone

    def commit_clone(self, clone, message):
        git(clone, "add", "-A")
        git(clone, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", message)

    def install_from(self, clone, *extra, check=True, tool="claude"):
        return run("python3", str(clone / "bin" / "install"), "--tool", tool, "--scope",
                   "project", str(self.root), *extra, check=check, env=self.env)

    def test_update_from_skill_files(self):
        clone = self.partitur_clone()
        for path in (clone / "project/skills").glob("*/SKILL.md.in"):
            path.rename(path.with_name("SKILL.md"))
        self.commit_clone(clone, "skill files before template rename")
        self.install_from(clone, "--records", "partitur-records", tool="all")
        link = self.root / ".agents/skills/partitur"
        self.assertEqual(len(skill_files(link.parent)), 1 + 2 * N_SKILLS)
        installed = {p: p.read_bytes() for p in link.parent.glob("ptt-*/SKILL.md")}
        claude_link = os.readlink(self.root / ".claude/skills/partitur")
        claude_hook = (self.root / ".claude/settings.json").read_bytes()
        for path in (clone / "project/skills").glob("*/SKILL.md"):
            path.rename(path.with_name("SKILL.md.in"))
        self.commit_clone(clone, "explicit skill templates")
        self.install_from(clone, "--records", "partitur-records", "--update", tool="all")
        self.assertEqual(link.resolve(), clone)
        self.assertEqual(len(skill_files(link.parent)), 1 + N_SKILLS)
        self.assertEqual({p: p.read_bytes() for p in installed}, installed)
        self.assertEqual(os.readlink(self.root / ".claude/skills/partitur"), claude_link)
        self.assertEqual((self.root / ".claude/settings.json").read_bytes(), claude_hook)
        self.assertEqual(git(clone, "status", "--porcelain"), "")
        self.install_from(clone, "--records", "partitur-records", "--uninstall", tool="all")
        self.assertFalse(link.is_symlink())
        self.assertEqual(skill_files(link.parent), [])
        self.assertTrue((self.root / "partitur-records/tasks/open/T0000-design/charter.md").is_file())
        self.assertEqual(git(clone, "status", "--porcelain"), "")

    def test_codex_preserves_replaced_entry(self):
        clone = self.partitur_clone()
        self.install_from(clone, tool="codex")
        link = self.root / ".agents/skills/partitur"
        link.unlink()
        custom = self.home / "custom-skill"
        custom.mkdir()
        (custom / "SKILL.md").write_text("my skill\n")
        for symlink in (True, False):
            with self.subTest(symlink=symlink):
                if symlink:
                    link.symlink_to(custom)
                else:
                    shutil.copytree(custom, link)
                self.install_from(clone, "--update", tool="codex")
                self.install_from(clone, "--uninstall", tool="codex")
                self.assertEqual((link / "SKILL.md").read_text(), "my skill\n")
                if symlink:
                    self.assertEqual(link.resolve(), custom)
                    link.unlink()
                else:
                    shutil.rmtree(link)

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

    def test_update_renames_rules_file(self):
        """A project installed when the rules file was <records>/CLAUDE.md:
        a plain rerun leaves it alone, --update renames it and relinks."""
        clone = self.partitur_clone()
        templates = clone / "templates"
        for name in ("rules.md", "root-charter.md"):
            path = templates / name
            path.write_text(path.read_text().replace("PROJECT-RULES.md", "CLAUDE.md"))
        self.commit_clone(clone, "rules file named CLAUDE.md")
        self.install_from(clone, tool="all")
        ws = self.root / "workspace"
        old, new = ws / "CLAUDE.md", ws / "PROJECT-RULES.md"
        old.write_text(old.read_text() + "\nSee workspace/CLAUDE.md for the deviations.\n")
        self.assertEqual(os.readlink(self.root / "AGENTS.md"), "workspace/CLAUDE.md")
        git(clone, "checkout", "-q", "HEAD~1", "--", "templates")
        self.commit_clone(clone, "rules file named PROJECT-RULES.md")
        out = self.install_from(clone, tool="all").stdout
        self.assertRegex(out, r"outdated\s+workspace/CLAUDE.md")
        self.assertFalse(new.exists())
        self.assertEqual(os.readlink(self.root / "CLAUDE.md"), "workspace/CLAUDE.md")
        out = self.install_from(clone, "--update", tool="all").stdout
        self.assertRegex(out, r"renamed\s+workspace/CLAUDE.md")
        self.assertRegex(out, r"updated\s+workspace/PROJECT-RULES.md")
        self.assertRegex(out, r"mentions\s+workspace/PROJECT-RULES.md")
        self.assertRegex(out, r"mentions\s+workspace/tasks/open/T0000-design/charter.md")
        self.assertFalse(old.exists())
        self.assertIn("See workspace/CLAUDE.md", new.read_text())
        self.assertIn("This file, `workspace/PROJECT-RULES.md`", new.read_text())
        for entry in ("CLAUDE.md", "AGENTS.md"):
            self.assertEqual(os.readlink(self.root / entry), "workspace/PROJECT-RULES.md")
        self.assertNotIn("renamed", self.install_from(clone, tool="all").stdout)
        self.install_from(clone, "--uninstall", tool="all")
        self.assertFalse((self.root / "CLAUDE.md").is_symlink())
        self.assertNotIn("partitur rules begin", new.read_text())

    def update_one_tool_after_rename(self, tool, other, custom=False):
        """Install for both tools when the rules file was <records>/CLAUDE.md,
        then --update for one tool only; return the other tool's entry."""
        clone = self.partitur_clone()
        for name in ("rules.md", "root-charter.md"):
            path = clone / "templates" / name
            path.write_text(path.read_text().replace("PROJECT-RULES.md", "CLAUDE.md"))
        self.commit_clone(clone, "rules file named CLAUDE.md")
        self.install_from(clone, tool="all")
        entry = self.root / other
        if custom:
            entry.unlink()
            entry.symlink_to("notes.md")
        git(clone, "checkout", "-q", "HEAD~1", "--", "templates")
        self.commit_clone(clone, "rules file named PROJECT-RULES.md")
        out = self.install_from(clone, "--update", tool=tool).stdout
        self.assertRegex(out, r"renamed\s+workspace/CLAUDE.md")
        self.assertEqual(os.readlink(self.root / {"claude": "CLAUDE.md", "codex": "AGENTS.md"}[tool]), "workspace/PROJECT-RULES.md")
        return entry, out

    def test_update_for_codex_relinks_claude_entry(self):
        entry, out = self.update_one_tool_after_rename("codex", "CLAUDE.md")
        self.assertRegex(out, r"relinked\s+CLAUDE.md")
        self.assertEqual(os.readlink(entry), "workspace/PROJECT-RULES.md")

    def test_update_for_claude_relinks_codex_entry(self):
        entry, out = self.update_one_tool_after_rename("claude", "AGENTS.md")
        self.assertRegex(out, r"relinked\s+AGENTS.md")
        self.assertEqual(os.readlink(entry), "workspace/PROJECT-RULES.md")

    def test_update_for_one_tool_keeps_custom_entry(self):
        entry, out = self.update_one_tool_after_rename("claude", "AGENTS.md", custom=True)
        self.assertNotIn("relinked", out)
        self.assertEqual(os.readlink(entry), "notes.md")

    def test_update_replaces_outdated_keeps_modified(self):
        clone = self.partitur_clone()
        out = self.install_from(clone).stdout
        stamp = (self.root / "workspace" / ".partitur-version").read_text()
        self.assertIn(git(clone, "rev-parse", "HEAD"), stamp)
        self.assertNotIn("uncommitted", out)
        ws = self.root / "workspace"
        mine = ws / "bin" / "test-run"
        mine.write_text(mine.read_text() + "\n# my change\n")
        rules = ws / "PROJECT-RULES.md"
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
        rules = self.root / "workspace" / "PROJECT-RULES.md"
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
        self.assertRegex(out, r"outdated\s+workspace/PROJECT-RULES.md")
        out = self.install_from(clone, "--update").stdout
        self.assertRegex(out, r"updated\s+workspace/PROJECT-RULES.md")
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
        self.assertRegex(out, r"removed\s+workspace/PROJECT-RULES.md")
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
        self.assertTrue((ws / "PROJECT-RULES.md").exists())
        self.assertTrue((task / "charter.md").exists())
        self.assertTrue(mine.exists())
        self.assertFalse((ws / ".partitur-version").exists())

    def test_codex_policy_files_follow_their_skills(self):
        """agents/openai.yaml beside a skill is delivered, updated, and
        removed like the skill; one changed here is kept."""
        clone = self.partitur_clone()
        shutil.rmtree(clone / "project/skills/ptt-take/agents")
        self.commit_clone(clone, "ptt-take without a policy file")
        self.install_from(clone, tool="codex")
        ws = self.root / "workspace"
        take, done = (ws / f"skills/{s}/agents/openai.yaml" for s in ("ptt-take", "ptt-done"))
        self.assertFalse(take.exists())
        self.assertIn("allow_implicit_invocation: false", done.read_text())
        self.assertFalse((ws / "skills/ptt-whoami/agents").exists())
        git(clone, "checkout", "-q", "HEAD~1", "--", "project/skills")
        self.commit_clone(clone, "ptt-take with a policy file")
        out = self.install_from(clone, "--update", tool="codex").stdout
        self.assertRegex(out, r"created\s+workspace/skills/ptt-take/agents/openai.yaml")
        self.assertEqual((self.root / ".agents/skills/ptt-take/agents/openai.yaml").read_text(),
                         take.read_text())
        done.write_text(done.read_text() + "# mine\n")
        out = self.install_from(clone, "--uninstall", tool="codex").stdout
        self.assertRegex(out, r"modified\s+workspace/skills/ptt-done/agents/openai.yaml")
        self.assertFalse((ws / "skills/ptt-take").exists())
        self.assertIn("# mine", done.read_text())

    def test_prompt_hook_merged_kept_and_removed(self):
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        mine = {"type": "command", "command": "echo mine"}
        settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]},
                                        "hooks": {"UserPromptSubmit": [{"hooks": [mine]}]}}))
        clone = self.partitur_clone()
        out = self.install_from(clone).stdout
        self.assertRegex(out, r"merged\s+\.claude/settings\.json")
        data = json.loads(settings.read_text())
        self.assertEqual(data["permissions"], {"allow": ["Bash(ls)"]})
        hooks = [h for e in data["hooks"]["UserPromptSubmit"] for h in e["hooks"]]
        self.assertIn(mine, hooks)
        self.assertIn('"$CLAUDE_PROJECT_DIR"/workspace/bin/ptt inbox --quiet',
                      [h["command"] for h in hooks])
        self.assertRegex(self.install_from(clone).stdout, r"kept\s+\.claude/settings\.json")
        out = self.install_from(clone, "--uninstall").stdout
        self.assertRegex(out, r"removed\s+\.claude/settings\.json")
        data = json.loads(settings.read_text())
        self.assertEqual(data["hooks"]["UserPromptSubmit"], [{"hooks": [mine]}])

    def test_prompt_hook_alone_is_removed_with_its_file(self):
        clone = self.partitur_clone()
        self.install_from(clone)
        settings = self.root / ".claude" / "settings.json"
        self.assertIn("ptt inbox --quiet", settings.read_text())
        self.install_from(clone, "--uninstall")
        self.assertFalse(settings.exists())

    def test_codex_hook_installs_runs_and_uninstalls(self):
        moved = self.root.with_name(self.root.name + " space's $project")
        self.root.rename(moved)
        self.root = moved
        clone = self.partitur_clone()
        self.install_from(clone, "--records", "records", tool="codex")
        settings = self.root / ".codex" / "hooks.json"
        command = json.loads(settings.read_text())["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        rec = self.root / "records"
        git(rec, "config", "user.name", "t")
        git(rec, "config", "user.email", "t@x")
        ptt = ["python3", str(rec / "bin" / "ptt")]
        env = dict(self.env, CODEX_THREAD_ID="codex-A")
        holder = run(*ptt, "take", "integrator", env=env).stdout.strip()
        run(*ptt, "free", "integrator", "--as", "user", "--reason", "test", env=self.env)
        event = json.dumps(dict(hook_event_name="UserPromptSubmit", session_id="codex-A"))
        result = subprocess.run(["sh", "-c", command], input=event, cwd=self.home,
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{holder} was freed", result.stdout)
        out = self.install_from(clone, "--records", "records", tool="codex").stdout
        self.assertRegex(out, r"kept\s+\.codex/hooks\.json")
        self.assertIn("review/trust", (self.root / "partitur-install-report.md").read_text())
        self.install_from(clone, "--records", "records", "--uninstall", tool="codex")
        self.assertFalse(settings.exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_hooks_keep_user_config_on_update_and_uninstall(self):
        clone = self.partitur_clone()
        for tool, rel in (("claude", ".claude/settings.json"), ("codex", ".codex/hooks.json")):
            with self.subTest(tool=tool):
                settings = self.root / rel
                settings.parent.mkdir(exist_ok=True)
                user = {"description": "my settings", "hooks": {"UserPromptSubmit": [
                    {"hooks": [{"type": "command", "command": "echo mine"}]}]}}
                settings.write_text(json.dumps(user))
                self.install_from(clone, tool=tool)
                installed = settings.read_text()
                data = json.loads(installed)
                data["hooks"]["UserPromptSubmit"][-1]["hooks"][0]["timeout"] = 17
                changed = json.dumps(data)
                settings.write_text(changed)
                self.assertIn("modified", self.install_from(clone, "--update", tool=tool).stdout)
                self.assertEqual(settings.read_text(), changed)
                self.assertIn("modified", self.install_from(clone, "--uninstall", tool=tool).stdout)
                self.assertEqual(settings.read_text(), changed)
                self.install_from(clone, tool=tool)
                backup = self.home / (tool + "-backup")
                self.install_from(clone, "--update", "--force", "--backup-to", str(backup), tool=tool)
                self.assertEqual((backup / rel).read_text(), changed)
                self.assertEqual(settings.read_text(), installed)
                self.install_from(clone, "--uninstall", tool=tool)
                self.assertEqual(json.loads(settings.read_text()), user)
                self.install_from(clone, tool=tool)
                settings.write_text(changed)
                backup = self.home / (tool + "-uninstall-backup")
                self.install_from(clone, "--uninstall", "--force", "--backup-to",
                                  str(backup), tool=tool)
                self.assertEqual((backup / rel).read_text(), changed)
                self.assertEqual(json.loads(settings.read_text()), user)

    def test_invalid_hook_settings_are_preserved(self):
        for tool, rel in (("claude", ".claude/settings.json"), ("codex", ".codex/hooks.json")):
            settings = self.root / rel
            settings.parent.mkdir(exist_ok=True)
            for value in ('{broken', '[]', '{"hooks": []}',
                          '{"hooks":{"UserPromptSubmit":{}}}',
                          '{"hooks":{"UserPromptSubmit":[{"hooks":[null]}]}}'):
                with self.subTest(tool=tool, value=value):
                    settings.write_text(value)
                    self.assertIn("not merged", self.install(tool=tool).stdout)
                    self.assertEqual(settings.read_text(), value)
                    self.assertIn("not merged", self.install("--uninstall", tool=tool).stdout)
                    self.assertEqual(settings.read_text(), value)

    def test_update_adds_codex_hook_to_previous_install(self):
        clone = self.partitur_clone()
        ptt = clone / "project" / "bin" / "ptt"
        current = ptt.read_text()
        ptt.write_text(current.replace("read_hook_session", "previous_hook_session"))
        self.commit_clone(clone, "before Codex hooks")
        self.install_from(clone, tool="all")
        settings = self.root / ".codex" / "hooks.json"
        self.assertFalse(settings.exists())
        claude = (self.root / ".claude" / "settings.json").read_bytes()
        ptt.write_text(current)
        self.commit_clone(clone, "Codex hooks")
        self.install_from(clone, "--update", tool="all")
        self.assertTrue(settings.is_file())
        self.assertEqual((self.root / ".claude" / "settings.json").read_bytes(), claude)
        self.install_from(clone, "--uninstall", tool="all")
        self.assertFalse(settings.exists())

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
                      (self.root / "workspace" / "PROJECT-RULES.md").read_text())
        again = self.install(tool="claude", cwd=self.root).stdout
        self.assertNotIn("found", again)

    def test_installed_skills_match_partitur(self):
        self.install()
        for skill in [p.name for p in (HERE / "project" / "skills").iterdir()]:
            src = (HERE / "project" / "skills" / skill / "SKILL.md.in").read_text()
            got = (self.root / "workspace" / "skills" / skill / "SKILL.md").read_text()
            self.assertEqual(got, src.replace("<records>", "workspace"))
        self.assertIn("https://github.com/", (self.root / "workspace" / "PROJECT-RULES.md").read_text())
        self.assertNotIn(str(HERE), (self.root / "workspace" / "PROJECT-RULES.md").read_text())

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

    def test_user_link_added_later_makes_project_link_redundant(self):
        self.install(tool="all")
        report = (self.root / "partitur-install-report.md").read_text()
        self.assertIn("--scope user --tool all", report)
        run("python3", str(INSTALL), "--scope", "user", "--tool", "all", env=self.env)
        out = self.install(tool="all").stdout
        self.assertRegex(out, r"redundant\s+\.agents/skills/partitur")
        self.assertRegex(out, r"redundant\s+\.claude/skills/partitur")
        self.assertTrue((self.root / ".agents/skills/partitur").is_symlink())
        self.assertNotIn("--scope user", (self.root / "partitur-install-report.md").read_text())
        self.assertRegex(self.install("--update", tool="all").stdout,
                         r"removed\s+\.agents/skills/partitur")
        self.assertFalse((self.root / ".agents/skills/partitur").is_symlink())
        self.assertFalse((self.root / ".claude/skills/partitur").is_symlink())
        project = skill_files(self.root / ".agents/skills")
        self.assertEqual(len(project) + 1, 1 + N_SKILLS)
        # uninstall also removes a redundant link left by an install without --update
        (self.root / ".agents/skills/partitur").symlink_to(HERE)
        self.install("--uninstall", tool="all")
        self.assertFalse((self.root / ".agents/skills/partitur").is_symlink())

    def test_codex_user_and_project_skills_do_not_overlap(self):
        run("python3", str(INSTALL), "--scope", "user", "--tool", "codex", env=self.env)
        self.install("--records", "partitur-records", tool="codex")
        project = self.root / ".agents/skills"
        user = self.home / ".agents/skills"
        found = skill_files(project) + skill_files(user)
        self.assertEqual(len(found), 1 + N_SKILLS)
        self.assertEqual(len({p.parent.name for p in found}), 1 + N_SKILLS)
        self.assertFalse((project / "partitur").exists())
        self.install("--records", "partitur-records", "--uninstall", tool="codex")
        self.assertEqual(skill_files(project), [])
        self.assertEqual(len(skill_files(user)), 1)

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
            self.assertEqual(len(skill_files(home / ".agents/skills")), 1)
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
