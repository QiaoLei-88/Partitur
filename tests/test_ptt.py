"""Tests for project/bin/ptt: roles, tasks, supervision, and concurrent claims,
in a temporary records repository.

Run: python3 -m unittest discover -s tests   (from the repository root)
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def run(*args, cwd=None, check=True, env=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if check and r.returncode:
        raise AssertionError(f"{args} failed: {r.stderr}")
    return r


class Ptt(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rec = self.root / "workspace"
        (self.rec / "bin").mkdir(parents=True)
        shutil.copy(HERE / "project" / "bin" / "ptt", self.rec / "bin" / "ptt")
        (self.rec / "tasks").mkdir()
        shutil.copy(HERE / "templates" / "charter.md", self.rec / "tasks" / "charter-template.md")
        run("git", "-C", str(self.rec), "init", "-q", "-b", "master")
        run("git", "-C", str(self.rec), "config", "user.email", "t@example.org")
        run("git", "-C", str(self.rec), "config", "user.name", "t")
        run("git", "-C", str(self.rec), "add", "-A")
        run("git", "-C", str(self.rec), "commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.root)

    def ptt(self, *args, check=True, env=None):
        return run("python3", str(self.rec / "bin" / "ptt"), *args, check=check, env=env)

    def fill(self, charter):
        charter.write_text(re.sub(r"\{\{[^}]*\}\}", "filled", charter.read_text()))

    def refused(self, *args):
        r = self.ptt(*args, check=False)
        self.assertNotEqual(r.returncode, 0, args)
        return r.stderr

    def designer(self):
        return self.ptt("take", "designer").stdout.strip()

    def task(self, slug, by, kind="track", depends=None):
        extra = ["--depends", depends] if depends else []
        path = Path(self.ptt("mktask", slug, "--as", by, "--kind", kind, *extra).stdout.strip())
        self.fill(path)
        number = path.parent.name.split("-")[0]
        self.ptt("ready", number, "--as", by)
        return number

    def test_role_conflicts_refused_and_generations(self):
        self.assertEqual(self.designer(), "designer-g1")
        self.assertIn("held by designer-g1", self.refused("take", "designer"))
        self.ptt("leave", "designer-g1")
        self.assertEqual(self.designer(), "designer-g2")
        self.assertEqual(self.ptt("take", "integrator").stdout.strip(), "integrator-1")
        self.assertIn("integrator  integrator-1", self.ptt("who").stdout)

    def test_task_lifecycle(self):
        d = self.designer()
        self.assertIn("not a designer", self.refused("mktask", "x", "--as", "track-9"))
        path = Path(self.ptt("mktask", "wall-distance", "--as", d).stdout.strip())
        self.assertEqual(path.parent.name, "0001-wall-distance")
        self.assertIn("kind: track", path.read_text())
        self.assertIn("Task 0001", path.read_text())
        self.assertIn("draft", self.refused("take", "0001"))
        self.assertIn("placeholders", self.refused("ready", "0001", "--as", d))
        self.fill(path)
        self.ptt("ready", "wall-distance", "--as", d)
        self.assertIn("is 0001-wall-distance", self.refused("take", "0001-other"))
        holder = self.ptt("take", "wall-distance").stdout.strip()
        self.assertEqual(holder, "track-0001")
        self.assertIn("held by track-0001", self.refused("take", "0001"))
        self.assertTrue((path.parent / "status.md").exists())
        me = self.ptt("whoami", holder).stdout
        self.assertIn("supervisor designer-g1", me)
        self.assertIn("no done report", self.refused("close", "0001", "--as", d))
        self.ptt("done", "0001", "--as", holder, "--requests", "000003")
        self.assertIn("reports done", self.ptt("whoami", d).stdout)
        self.assertIn("does not supervise", self.refused("close", "0001", "--as", "integrator-1"))
        self.ptt("close", "0001", "--as", d)
        self.assertTrue((self.rec / "tasks" / "done" / "0001-wall-distance").is_dir())
        listing = self.ptt("tasks", "--all").stdout
        self.assertIn("closed", listing)
        self.assertNotIn("done reported", listing)
        self.assertIn("holds nothing", self.ptt("whoami", holder).stdout)
        for args in (("done", "1", "--as", holder), ("reopen", "1", "--as", d, "--reason", "x"),
                     ("amend", "1", "--as", d, "--text", "x"), ("take", "1"),
                     ("cancel", "1", "--as", d, "--reason", "x")):
            self.refused(*args)
        log = run("git", "-C", str(self.rec), "log", "--format=%s").stdout
        self.assertIn("task 0001: taken by track-0001", log)
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_leave_needs_supervisor_and_clear_subordinates(self):
        d = self.designer()
        n = self.task("probe", d)
        holder = self.ptt("take", n).stdout.strip()
        self.ptt("leave", holder, "--status", "half done; see status.md")
        self.assertIn("asks to leave", self.ptt("whoami", d).stdout)
        self.assertIn("waiting: your request to leave", self.ptt("whoami", holder).stdout)
        self.assertIn("already asked", self.refused("leave", holder))
        self.assertIn("asks to leave", self.refused("leave", d))
        self.ptt("approve-leave", n, "--as", d)
        self.assertEqual(self.ptt("take", n).stdout.strip(), "track-0001-2")
        self.ptt("leave", d)

    def test_supervisor_frees_a_gone_holder_and_user_frees_a_role(self):
        d = self.designer()
        n = self.task("probe", d)
        self.ptt("take", n)
        self.assertIn("does not supervise", self.refused("free", n, "--as", "track-7",
                                                          "--reason", "x"))
        self.assertIn("may still be working", self.refused("free", n, "--as", d, "--reason", "x"))
        self.ptt("free", n, "--as", d, "--reason", "session gone", "--force")
        self.assertIn("ready", self.ptt("tasks").stdout)
        self.assertIn("only the user", self.refused("free", "designer", "--as", d, "--reason", "x"))
        self.ptt("free", "designer", "--as", "user", "--reason", "session crashed")
        self.assertEqual(self.designer(), "designer-g2")

    def test_sub_designer_scope(self):
        d = self.designer()
        n = self.task("adapter", d, kind="design")
        sub = self.ptt("take", n).stdout.strip()
        self.assertEqual(sub, "design-0001")
        child = self.task("indexing", sub)
        self.assertEqual(child, "0001.1")
        self.assertIn("does not supervise", self.refused("close", child, "--as", d))
        w = self.ptt("take", child).stdout.strip()
        self.assertIn("supervisor design-0001", self.ptt("whoami", w).stdout)
        self.ptt("done", n, "--as", sub)
        self.assertIn("subtasks are not closed", self.refused("close", n, "--as", d))
        self.ptt("done", child, "--as", w)
        self.assertIn("reports done", self.refused("leave", sub))
        self.ptt("close", child, "--as", sub)
        self.ptt("close", n, "--as", d)

    def test_dependencies_block(self):
        d = self.designer()
        first = self.task("first", d)
        second = self.task("second", d, depends="1")
        self.assertIn("depends: 0001", (self.rec / "tasks" / "open" / "0002-second" /
                                        "charter.md").read_text())
        self.assertIn("waits for 0001", self.ptt("tasks").stdout)
        self.assertIn("blocked", self.refused("take", second))
        h = self.ptt("take", first).stdout.strip()
        self.ptt("done", first, "--as", h)
        self.ptt("close", first, "--as", d)
        self.assertEqual(self.ptt("take", second).stdout.strip(), "track-0002")

    def test_cancel_and_reopen(self):
        d = self.designer()
        n = self.task("x", d)
        h = self.ptt("take", n).stdout.strip()
        self.assertIn("free it first", self.refused("cancel", n, "--as", d, "--reason", "r"))
        self.ptt("done", n, "--as", h)
        self.ptt("reopen", n, "--as", d, "--reason", "acceptance 2 not met")
        self.assertNotIn("reports done", self.ptt("whoami", d).stdout)
        self.ptt("free", n, "--as", d, "--reason", "rethink", "--force")
        self.ptt("cancel", n, "--as", d, "--reason", "superseded")
        self.assertTrue(any((self.rec / "tasks" / "cancelled").iterdir()))

    def test_integrator_cannot_leave_with_decision_not_carried_out(self):
        self.ptt("take", "integrator")
        d = self.rec / "pr" / "open" / "000001-x"
        d.mkdir(parents=True)
        (d / "0002-decision.md").write_text("---\nkind: decision\ndecision: merge\n---\n")
        self.assertIn("not carried out", self.refused("leave", "integrator-1"))
        (d / "0002-decision.md").write_text("---\nkind: decision\ndecision: changes-requested\n---\n")
        self.ptt("leave", "integrator-1")

    def test_concurrent_take_has_one_winner(self):
        d = self.designer()
        n = self.task("race", d)
        procs = [subprocess.Popen(["python3", str(self.rec / "bin" / "ptt"), "take", n],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for _ in range(4)]
        codes = [p.communicate() and p.returncode for p in procs]
        self.assertEqual(codes.count(0), 1, codes)
        takes = list((self.rec / "tasks" / "open").glob("*/[0-9][0-9][0-9][0-9]-take.md"))
        self.assertEqual(len(takes), 1)

    def test_concurrent_role_take_has_one_winner(self):
        procs = [subprocess.Popen(["python3", str(self.rec / "bin" / "ptt"), "take", "designer"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for _ in range(4)]
        codes = [p.communicate() and p.returncode for p in procs]
        self.assertEqual(codes.count(0), 1, codes)

    def test_take_and_cancel_race_stays_consistent(self):
        d = self.designer()
        for k in range(6):
            n = self.task(f"r{k}", d)
            ptt = str(self.rec / "bin" / "ptt")
            procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for cmd in (["python3", ptt, "take", n],
                                 ["python3", ptt, "cancel", n, "--as", d, "--reason", "x"])]
            codes = [p.communicate() and p.returncode for p in procs]
            self.assertEqual(sorted(codes)[0], 0)
            self.assertNotEqual(sorted(codes)[1], 0, codes)
            line = [l for l in self.ptt("tasks", "--all").stdout.splitlines() if l.startswith(n)][0]
            self.assertIn("cancelled" if codes[1] == 0 else "held", line)
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_unclear_subtree_blocks_leaving(self):
        d = self.designer()
        n = self.task("adapter", d, kind="design")
        sub = self.ptt("take", n).stdout.strip()
        mid = self.task("part", sub, kind="design")
        midh = self.ptt("take", mid).stdout.strip()
        leaf = self.task("leaf", midh)
        leafh = self.ptt("take", leaf).stdout.strip()
        self.ptt("leave", leafh)
        self.assertIn("asks to leave", self.refused("leave", d))
        self.assertIn("asks to leave", self.refused("leave", sub))
        self.ptt("approve-leave", leaf, "--as", midh)
        self.ptt("leave", sub)
        self.ptt("approve-leave", n, "--as", d)
        self.assertIn("vacant", self.ptt("whoami", midh).stdout)
        self.assertIn("is held", self.refused("cancel", n, "--as", d, "--reason", "x")
                      .replace("not finished", "is held"))

    def test_stale_holder_is_listed_and_blocks(self):
        d = self.designer()
        n = self.task("slow", d)
        old = dict(os.environ, GIT_COMMITTER_DATE="2020-01-01T00:00:00",
                   GIT_AUTHOR_DATE="2020-01-01T00:00:00")
        h = self.ptt("take", n, env=old).stdout.strip()
        self.assertIn(f"no record from {h}", self.ptt("whoami", d).stdout)
        self.assertIn("no record", self.refused("leave", d))
        self.ptt("free", n, "--as", d, "--reason", "gone")
        self.ptt("leave", d)

    def test_field_values_without_line_breaks(self):
        d = self.designer()
        n = self.task("x", d)
        h = self.ptt("take", n).stdout.strip()
        self.assertIn("line breaks", self.refused("done", n, "--as", h, "--requests", "1\nby: x"))
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_record_alongside_task_changes(self):
        d = self.designer()
        notes = self.rec / "notes.txt"
        script = ("for i in $(seq 40); do echo $i >> notes.txt; "
                  f"python3 {self.rec / 'bin' / 'ptt'} record -m n$i notes.txt >/dev/null; done")
        loop = subprocess.Popen(["sh", "-c", script], cwd=self.rec)
        for k in range(12):
            self.ptt("mktask", f"t{k}", "--as", d)
        loop.wait()
        git = lambda *a: run("git", "-C", str(self.rec), *a).stdout
        tracked = git("ls-tree", "-r", "--name-only", "HEAD")
        for k in range(12):
            self.assertIn(f"tasks/open/{k + 1:04d}-t{k}/charter.md", tracked)
        self.assertEqual(git("status", "--porcelain"), "")
        self.assertEqual(git("log", "-1", "--format=%s", "--", "notes.txt").strip(), "n40")
        self.assertEqual(loop.returncode, 0)

    def test_failed_record_leaves_nothing(self):
        d = self.designer()
        (self.rec / ".git" / "index.lock").write_text("")
        env = dict(os.environ, PTT_LOCK_WAIT="0.5")
        r = run("python3", str(self.rec / "bin" / "ptt"), "mktask", "x", "--as", d,
                check=False, env=env)
        (self.rec / ".git" / "index.lock").unlink()
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.rec / "tasks" / "open" / "0001-x").exists())
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_close_with_uncommitted_status_changes_nothing(self):
        d = self.designer()
        n = self.task("x", d)
        h = self.ptt("take", n).stdout.strip()
        self.ptt("done", n, "--as", h)
        status = next((self.rec / "tasks" / "open").glob("0001-*/status.md"))
        status.write_text(status.read_text() + "more\n")
        self.assertIn("uncommitted", self.refused("close", n, "--as", d))
        self.assertIn("done reported", self.ptt("tasks").stdout)
        run("git", "-C", str(self.rec), "commit", "-qam", "status")
        self.ptt("close", n, "--as", d)
        self.assertTrue((self.rec / "tasks" / "done" / status.parent.name).is_dir())
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_dependency_rules(self):
        d = self.designer()
        a = self.task("a", d)
        b = self.task("b", d, depends="a")
        self.assertIn("cycle", self.refused("amend", a, "--as", d, "--text", "x", "--depends", b))
        self.assertIn("itself", self.refused("amend", b, "--as", d, "--text", "x", "--depends", b))
        self.assertIn("depend on it", self.refused("cancel", a, "--as", d, "--reason", "x"))
        design = self.task("parent", d, kind="design")
        sub = self.ptt("take", design).stdout.strip()
        self.assertIn("contains it", self.refused("mktask", "c", "--as", sub, "--depends", design))
        path = Path(self.ptt("mktask", "e", "--as", d, "--depends", "1, a ,0001").stdout.strip())
        self.assertIn("depends: 0001\n", path.read_text())

    def test_names_and_free_with_done(self):
        d = self.designer()
        n = self.task("same", d)
        self.assertIn("already named", self.refused("mktask", "same", "--as", d))
        self.assertIn("starts with a letter", self.refused("mktask", "7-x", "--as", d))
        h = self.ptt("take", n).stdout.strip()
        self.ptt("done", n, "--as", h)
        self.assertIn("close or reopen", self.refused("free", n, "--as", d, "--reason", "x"))
        self.ptt("reopen", n, "--as", d, "--reason", "x")
        self.ptt("free", n, "--as", d, "--reason", "x", "--force")
        self.ptt("cancel", n, "--as", d, "--reason", "x")
        again = self.task("same", d)
        self.assertEqual(self.ptt("take", "same").stdout.strip(), f"track-{again}")

    def test_record_keeps_other_staged_changes(self):
        (self.rec / "a.txt").write_text("a\n")
        (self.rec / "b.txt").write_text("b\n")
        run("git", "-C", str(self.rec), "add", "b.txt")
        self.assertEqual(self.ptt("record", "-m", "a only", str(self.rec / "a.txt")).stdout.strip(),
                         "recorded")
        self.assertIn("A  b.txt", run("git", "-C", str(self.rec), "status", "--porcelain").stdout)
        self.assertIn("outside", self.refused("record", "-m", "x", "/etc/hostname"))

    def test_loose_task_files_are_reported(self):
        d = self.designer()
        stray = self.rec / "tasks" / "open" / "0009-stray"
        stray.mkdir(parents=True)
        (stray / "charter.md").write_text("x\n")
        out = self.ptt("tasks").stdout
        self.assertIn("uncommitted in the records repository", out)
        self.assertIn("  tasks/open/0009-stray/charter.md", out)

    def test_cancel_refuses_uncommitted_task_content(self):
        d = self.designer()
        n = self.task("x", d)
        (next((self.rec / "tasks" / "open").glob("0001-*")) / "notes.tmp").write_text("x\n")
        self.assertIn("uncommitted changes", self.refused("cancel", n, "--as", d, "--reason", "r"))

    def test_records_worktree(self):
        wt = self.root / "wt"
        run("git", "-C", str(self.rec), "worktree", "add", "-q", str(wt))
        r = run("python3", str(wt / "bin" / "ptt"), "take", "designer", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("primary checkout", r.stderr)
        self.assertEqual(run("git", "-C", str(wt), "status", "--porcelain").stdout, "")

    def test_stray_write_after_move_refused(self):
        req = self.rec / "pr" / "open" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text("x\n")
        self.ptt("record", "-m", "submit", str(req))
        merged = self.rec / "pr" / "merged" / "000001-x"
        self.assertIn("moved to pr/merged", self.ptt("pr-move", "1", "merged", "-m", "merged").stdout)
        self.assertTrue((merged / "0001-request.md").exists())
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")
        req.mkdir()
        (req / "0004-reply.md").write_text("late\n")
        self.assertIn("now pr/merged/000001-x", self.refused("record", "-m", "reply",
                                                             str(req / "0004-reply.md")))


if __name__ == "__main__":
    unittest.main()
