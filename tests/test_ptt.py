"""Tests for project/bin/ptt: roles, tasks, supervision, and concurrent claims,
in a temporary records repository.

Run: python3 -m unittest discover -s tests   (from the repository root)
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def run(*args, cwd=None, check=True, env=None, input=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, input=input)
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
        root = self.rec / "tasks" / "open" / "T0000-design"
        root.mkdir(parents=True)
        shutil.copy(HERE / "templates" / "root-charter.md", root / "charter.md")
        run("git", "-C", str(self.rec), "init", "-q", "-b", "master")
        run("git", "-C", str(self.rec), "config", "user.email", "t@example.org")
        run("git", "-C", str(self.rec), "config", "user.name", "t")
        run("git", "-C", str(self.rec), "add", "-A")
        run("git", "-C", str(self.rec), "commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.root)

    def env(self, base=None, session=None):
        """The environment of a session with the given ID (none by default)."""
        env = dict(os.environ if base is None else base)
        for key in ("PTT_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID",
                    "CODEX_SESSION_ID"):
            env.pop(key, None)
        if session:
            env["PTT_SESSION_ID"] = session
        return env

    def ptt(self, *args, check=True, env=None, session=None):
        env = self.env(env, session)
        return run("python3", str(self.rec / "bin" / "ptt"), *args, check=check, env=env)

    def fill(self, charter):
        charter.write_text(re.sub(r"\{\{[^}]*\}\}", "filled", charter.read_text()))

    def refused(self, *args, session=None):
        r = self.ptt(*args, check=False, session=session)
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
        self.assertEqual(path.parent.name, "T0001-wall-distance")
        self.assertIn("kind: track", path.read_text())
        self.assertIn("Task T0001", path.read_text())
        self.assertIn("draft", self.refused("take", "T0001"))
        self.assertIn("placeholders", self.refused("ready", "T0001", "--as", d))
        self.fill(path)
        self.ptt("ready", "wall-distance", "--as", d)
        self.assertIn("is T0001-wall-distance", self.refused("take", "T0001-other"))
        holder = self.ptt("take", "wall-distance").stdout.strip()
        self.assertEqual(holder, "track-T0001")
        self.assertIn("held by track-T0001", self.refused("take", "T0001"))
        self.assertTrue((path.parent / "status.md").exists())
        me = self.ptt("whoami", holder).stdout
        self.assertIn("supervisor designer-g1", me)
        self.assertIn("no done report", self.refused("close", "T0001", "--as", d))
        self.ptt("done", "T0001", "--as", holder, "--requests", "000003")
        self.assertIn("reports done", self.ptt("inbox", d).stdout)
        self.assertIn("does not supervise", self.refused("close", "T0001", "--as", "integrator-1"))
        self.ptt("close", "T0001", "--as", d)
        self.assertTrue((self.rec / "tasks" / "done" / "T0001-wall-distance").is_dir())
        listing = self.ptt("tasks", "--all").stdout
        self.assertIn("closed", listing)
        self.assertNotIn("done reported", listing)
        self.assertIn("holds nothing", self.ptt("whoami", holder).stdout)
        for args in (("done", "1", "--as", holder), ("reopen", "1", "--as", d, "--reason", "x"),
                     ("amend", "1", "--as", d, "--text", "x"), ("take", "1"),
                     ("cancel", "1", "--as", d, "--reason", "x")):
            self.refused(*args)
        log = run("git", "-C", str(self.rec), "log", "--format=%s").stdout
        self.assertIn("task T0001: taken by track-T0001", log)
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_leave_needs_supervisor_and_clear_subordinates(self):
        d = self.designer()
        n = self.task("probe", d)
        holder = self.ptt("take", n).stdout.strip()
        self.ptt("leave", holder, "--status", "half done; see status.md")
        self.assertIn("asks to leave", self.ptt("inbox", d).stdout)
        self.assertIn("your request to leave waits", self.ptt("inbox", holder).stdout)
        self.assertIn("already asked", self.refused("leave", holder))
        self.assertIn("asks to leave", self.refused("leave", d))
        self.ptt("approve-leave", n, "--as", d)
        self.assertEqual(self.ptt("take", n).stdout.strip(), "track-T0001-2")
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
        self.assertIn("its supervisor is user",
                      self.refused("free", "designer", "--as", d, "--reason", "x"))
        self.assertIn("may still be working",
                      self.refused("free", "designer", "--as", "user", "--reason", "x"))
        self.ptt("free", "designer", "--as", "user", "--reason", "session crashed", "--force")
        self.assertEqual(self.designer(), "designer-g2")
        self.assertIn("level 0, generation 2", self.ptt("whoami", "designer-g2").stdout)
        self.assertIn("only the user", self.refused("free", "integrator", "--as", d,
                                                    "--reason", "x"))

    def test_root_design_task_stays_open(self):
        d = self.designer()
        self.assertIn("level 0, generation 1", self.ptt("whoami", d).stdout)
        self.assertIn("supervisor user", self.ptt("whoami", d).stdout)
        for args in (("done", "T0000", "--as", d), ("close", "designer", "--as", "user"),
                     ("cancel", "0", "--as", "user", "--reason", "x")):
            self.assertIn("root design", self.refused(*args))
        self.assertIn("designer    designer-g1", self.ptt("who").stdout)
        self.ptt("amend", "T0000", "--as", "user", "--text", "design document moved")
        self.assertIn("does not supervise", self.refused("amend", "T0000", "--as", d,
                                                         "--text", "x"))

    def test_notes_on_unfilled_root_and_missing_integrator(self):
        r = self.ptt("take", "designer")
        self.assertEqual(r.stdout.strip(), "designer-g1")
        self.assertIn("T0000 is not filled in yet (charter.md", r.stderr)
        self.assertIn("fill them in place", r.stderr)
        self.assertIn("no session holds the integrator role", r.stderr)
        req = self.rec / "pr" / "open" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text("x\n")
        r = self.ptt("record", "-m", "submit", str(req))
        self.assertIn("request 000001-x waits", r.stderr)
        (req / "0002-reply.md").write_text("x\n")
        self.assertNotIn("integrator", self.ptt("record", "-m", "reply", str(req)).stderr)
        self.ptt("take", "integrator")
        req2 = self.rec / "pr" / "open" / "000002-y"
        req2.mkdir()
        (req2 / "0001-request.md").write_text("x\n")
        self.assertEqual(self.ptt("record", "-m", "submit", str(req2)).stderr, "")
        self.ptt("leave", "designer-g1")
        charter = self.rec / "tasks" / "open" / "T0000-design" / "charter.md"
        self.fill(charter)
        self.fill(charter.parent / "status.md")
        self.ptt("record", "-m", "fill", str(charter.parent))
        self.assertEqual(self.ptt("take", "designer", session="S").stderr, "")

    def test_record_and_pr_move_accept_as(self):
        req = self.rec / "pr" / "open" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text("x\n")
        self.ptt("record", "-m", "pr 000001: submit", "--as", "track-T0001", str(req))
        self.ptt("pr-move", "1", "merged", "-m", "pr 000001: merged", "--as", "integrator-1")
        log = run("git", "-C", str(self.rec), "log", "--format=%s").stdout
        self.assertIn("pr 000001: submit (by track-T0001)", log)
        self.assertIn("pr 000001: merged (by integrator-1)", log)

    def test_holder_sees_amendments_since_its_take(self):
        d = self.designer()
        n = self.task("probe", d)
        self.ptt("amend", n, "--as", d, "--text", "before the take")
        holder = self.ptt("take", n).stdout.strip()
        self.assertNotIn("amended", self.ptt("inbox", holder).stdout)
        self.ptt("amend", n, "--as", d, "--text", "scope narrowed")
        out = self.ptt("inbox", holder).stdout
        self.assertRegex(out, r"amended since your take: \d{4}-amend.md; read it with `ptt show T0001`")
        self.ptt("leave", holder)
        self.ptt("approve-leave", n, "--as", d)
        self.assertNotIn("amended", self.ptt("inbox", self.ptt("take", n).stdout.strip()).stdout)

    def test_root_task_has_no_dependencies(self):
        d = self.designer()
        self.assertIn("never closes", self.refused("mktask", "x", "--as", d, "--depends", "T0000"))
        self.task("first", d)
        self.assertIn("no dependencies", self.refused("amend", "T0000", "--as", "user",
                                                      "--text", "x", "--depends", "T0001"))

    def test_reserved_slugs_and_hand_written_depends(self):
        d = self.designer()
        for slug in ("designer", "integrator", "t1", "t2-x"):
            self.assertIn("reserved", self.refused("mktask", slug, "--as", d))
        self.task("first", d)
        path = Path(self.ptt("mktask", "second", "--as", d).stdout.strip())
        self.fill(path)
        path.write_text(path.read_text().replace("depends: \n", "depends: t1\n"))
        self.ptt("ready", "second", "--as", d)
        self.assertIn("waits for T0001", self.ptt("tasks").stdout)
        path = Path(self.ptt("mktask", "third", "--as", d).stdout.strip())
        self.fill(path)
        path.write_text(path.read_text().replace("depends: \n", "depends: first\n"))
        self.assertIn("as task IDs: T0001", self.refused("ready", "third", "--as", d))

    def test_earlier_formats_and_missing_root_refused(self):
        old = self.rec / "tasks" / "open" / "0001-old"
        old.mkdir()
        self.assertIn("earlier Partitur format", self.refused("tasks"))
        old.rmdir()
        roles = self.rec / "roles" / "designer"
        roles.mkdir(parents=True)
        (roles / "0001-take.md").write_text("---\nby: designer-g1\n---\n")
        self.assertIn("roles/designer/", self.refused("who"))
        shutil.rmtree(roles)
        shutil.rmtree(self.rec / "tasks" / "open" / "T0000-design")
        self.assertIn("run Partitur's install", self.refused("take", "designer"))

    def test_sub_designer_scope(self):
        d = self.designer()
        n = self.task("adapter", d, kind="design")
        sub = self.ptt("take", n).stdout.strip()
        self.assertEqual(sub, "design-T0001")
        child = self.task("indexing", sub)
        self.assertEqual(child, "T0001.1")
        self.assertIn("does not supervise", self.refused("close", child, "--as", d))
        w = self.ptt("take", child).stdout.strip()
        self.assertIn("supervisor design-T0001", self.ptt("whoami", w).stdout)
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
        self.assertIn("depends: T0001", (self.rec / "tasks" / "open" / "T0002-second" /
                                        "charter.md").read_text())
        self.assertIn("waits for T0001", self.ptt("tasks").stdout)
        self.assertIn("blocked", self.refused("take", second))
        h = self.ptt("take", first).stdout.strip()
        self.ptt("done", first, "--as", h)
        self.ptt("close", first, "--as", d)
        self.assertEqual(self.ptt("take", second).stdout.strip(), "track-T0002")

    def test_cancel_and_reopen(self):
        d = self.designer()
        n = self.task("x", d)
        h = self.ptt("take", n).stdout.strip()
        self.assertIn("free it first", self.refused("cancel", n, "--as", d, "--reason", "r"))
        self.ptt("done", n, "--as", h)
        self.ptt("reopen", n, "--as", d, "--reason", "acceptance 2 not met")
        self.assertNotIn("reports done", self.ptt("inbox", d).stdout)
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
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  env=self.env())
                 for _ in range(4)]
        codes = [p.communicate() and p.returncode for p in procs]
        self.assertEqual(codes.count(0), 1, codes)
        takes = list((self.rec / "tasks" / "open").glob("T0001-*/[0-9][0-9][0-9][0-9]-take.md"))
        self.assertEqual(len(takes), 1)

    def test_concurrent_role_take_has_one_winner(self):
        procs = [subprocess.Popen(["python3", str(self.rec / "bin" / "ptt"), "take", "designer"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  env=self.env())
                 for _ in range(4)]
        codes = [p.communicate() and p.returncode for p in procs]
        self.assertEqual(codes.count(0), 1, codes)

    def test_take_and_cancel_race_stays_consistent(self):
        d = self.designer()
        for k in range(6):
            n = self.task(f"r{k}", d)
            ptt = str(self.rec / "bin" / "ptt")
            procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                      env=self.env())
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
        self.assertIn(f"no record from {h}", self.ptt("inbox", d).stdout)
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
            self.ptt("mktask", f"s{k}", "--as", d)
        loop.wait()
        git = lambda *a: run("git", "-C", str(self.rec), *a).stdout
        tracked = git("ls-tree", "-r", "--name-only", "HEAD")
        for k in range(12):
            self.assertIn(f"tasks/open/T{k + 1:04d}-s{k}/charter.md", tracked)
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
        self.assertFalse((self.rec / "tasks" / "open" / "T0001-x").exists())
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_close_with_uncommitted_status_changes_nothing(self):
        d = self.designer()
        n = self.task("x", d)
        h = self.ptt("take", n).stdout.strip()
        self.ptt("done", n, "--as", h)
        status = next((self.rec / "tasks" / "open").glob("T0001-*/status.md"))
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
        self.assertIn("depends: T0001\n", path.read_text())

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
        stray = self.rec / "tasks" / "open" / "T0009-stray"
        stray.mkdir(parents=True)
        (stray / "charter.md").write_text("x\n")
        out = self.ptt("tasks").stdout
        self.assertIn("uncommitted in the records repository", out)
        self.assertIn("  tasks/open/T0009-stray/charter.md", out)

    def test_cancel_refuses_uncommitted_task_content(self):
        d = self.designer()
        n = self.task("x", d)
        (next((self.rec / "tasks" / "open").glob("T0001-*")) / "notes.tmp").write_text("x\n")
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


    def test_sessions_bind_holders(self):
        d = self.ptt("take", "designer", session="A").stdout.strip()
        n = self.task("wall-distance", d)
        self.assertIn("this session is designer-g1", self.refused("take", n, session="A"))
        self.assertEqual(self.ptt("whoami", session="A").stdout.split(":")[0], d)
        self.assertIn("session: this one", self.ptt("whoami", d, session="A").stdout)
        self.assertIn("holds nothing", self.ptt("whoami", session="B").stdout)
        # after /clear the session has a new ID: writes as d are refused until resumed
        self.assertIn("bound to another session", self.refused(
            "mktask", "x", "--as", d, session="B"))
        self.assertIn("another one", self.ptt("whoami", d, session="B").stdout)
        r = self.ptt("resume", d, session="B")
        self.assertIn(f"this session is {d}", r.stdout)
        self.assertIn("must no longer be used", r.stderr)
        self.ptt("mktask", "x", "--as", d, session="B")
        # the old session is refused, also for a plain record without --as
        self.assertIn("continued in another session", self.refused(
            "mktask", "y", "--as", d, session="A"))
        status = self.rec / "tasks" / "open" / "T0000-design" / "status.md"
        status.write_text("x\n")
        self.assertIn("continued in another session", self.refused(
            "record", "-m", "s", str(status), session="A"))
        self.ptt("record", "-m", "s", str(status), session="B")
        # resume refuses a name that holds nothing and a session that holds another
        self.assertIn("holds nothing", self.refused("resume", "worker-T0999", session="C"))
        w = self.ptt("take", n, session="C").stdout.strip()
        self.assertIn(f"this session is {w}", self.refused("resume", d, session="C"))
        self.assertIn("already", self.ptt("resume", w, session="C").stdout)
        # the user, and sessions without an ID, are not checked
        self.ptt("mktask", "z", "--as", d)
        self.assertIn("holds nothing that ptt can see", self.ptt("whoami").stdout)

    def test_native_sessions_bind_resume_and_refuse_old_writes(self):
        for key in ("CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID", "CODEX_SESSION_ID"):
            with self.subTest(key=key):
                env_a = dict(self.env(), **{key: key + "-A"})
                env_b = dict(self.env(), **{key: key + "-B"})

                def native(*args, env=env_a, check=True):
                    return run("python3", str(self.rec / "bin" / "ptt"), *args,
                               env=env, check=check)

                holder = native("take", "integrator").stdout.strip()
                self.assertIn(holder, native("whoami").stdout)
                self.assertIn("one session holds one", native(
                    "take", "designer", check=False).stderr)
                self.assertIn("bound to another session", native(
                    "leave", holder, env=env_b, check=False).stderr)
                self.assertIn("already", native("resume", holder).stdout)
                native("resume", holder, env=env_b)
                self.assertIn("continued in another session", native(
                    "leave", holder, check=False).stderr)
                status = self.rec / "handoff" / "integrator.md"
                status.parent.mkdir(exist_ok=True)
                status.write_text(key + "\n")
                self.assertIn("continued in another session", native(
                    "record", "-m", "handover", str(status), check=False).stderr)
                native("record", "-m", "handover", str(status), env=env_b)
                native("leave", holder, env=env_b)

    def test_session_environment_precedence(self):
        keys = ("PTT_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID",
                "CODEX_SESSION_ID")
        env = dict(self.env(), **{key: key for key in keys})
        ptt = ["python3", str(self.rec / "bin" / "ptt")]
        for key in (*keys, None):
            with self.subTest(key=key):
                holder = run(*ptt, "take", "integrator", env=env).stdout.strip()
                take = sorted((self.rec / "roles" / "integrator").glob("*-take.md"))[-1]
                if key is None:
                    self.assertNotIn("session_id:", take.read_text())
                else:
                    self.assertIn(f"\nsession_id: {key}\n", take.read_text())
                run(*ptt, "leave", holder, env=env)
                if key is not None:
                    env[key] = ""

    def test_inbox_hook_uses_event_identity_and_keeps_override(self):
        holder = self.ptt("take", "designer", session="D").stdout.strip()
        task = self.task("hook", holder)
        worker = self.ptt("take", task, session="W").stdout.strip()
        self.ptt("amend", task, "--as", holder, "--text", "new requirement", session="D")

        def hook(payload, env=None, quiet=True):
            return run("python3", str(self.rec / "bin" / "ptt"), "inbox", "--hook",
                       *(["--quiet"] if quiet else []), input=payload, check=False,
                       env=self.env() if env is None else env)

        event = json.dumps(dict(hook_event_name="UserPromptSubmit", session_id="W"))
        for bad in ("not json", "[]", "{}", '{"session_id":"W"}',
                    '{"hook_event_name":"UserPromptSubmit","session_id":123}',
                    '{"hook_event_name":"UserPromptSubmit","session_id":""}'):
            result = hook(bad)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertIn("expected", hook("{}", quiet=False).stderr)
        env = dict(self.env(), CODEX_THREAD_ID="wrong", CODEX_SESSION_ID="wrong")
        result = hook(event, env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn(f"ptt inbox for {worker}", result.stdout)
        self.assertIn("amend event", result.stdout)
        self.assertEqual(hook(event).stdout, "")
        self.ptt("amend", task, "--as", holder, "--text", "another requirement", session="D")
        wrong = json.dumps(dict(hook_event_name="UserPromptSubmit", session_id="wrong"))
        self.assertIn("amend event", hook(wrong, env=self.env(session="W")).stdout)
        self.ptt("done", task, "--as", worker, session="W")
        self.ptt("close", task, "--as", holder, session="D")
        self.assertIn("was closed", hook(event).stdout)
        self.assertEqual(hook(event).stdout, "")

    def test_inbox_shows_what_is_new_once(self):
        d = self.ptt("take", "designer", session="D").stdout.strip()
        n = self.task("probe", d)
        w = self.ptt("take", n, session="W").stdout.strip()
        i = self.ptt("take", "integrator", session="I").stdout.strip()
        for who in (d, w, i):
            self.ptt("inbox", who)                      # first look: sets the marker
        status = next((self.rec / "tasks" / "open").glob("T0001-*")) / "status.md"
        status.write_text("finding for the designer\n")
        self.ptt("record", "-m", "T0001 status", str(status), session="W")
        note = self.rec / "handoff" / "notes" / "t0001-x.md"
        note.parent.mkdir(parents=True)
        note.write_text("x\n")
        self.ptt("record", "-m", "note", str(note), session="W")
        req = self.rec / "pr" / "open" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text(f"---\nkind: request\nsession: {w}\n---\n")
        self.ptt("record", "-m", "pr 000001: submit", str(req), session="W")
        out = self.ptt("inbox", session="D").stdout     # the holder bound to the session
        self.assertIn("read T0001 status.md: updated by its holder", out)
        self.assertIn("read handoff/notes/t0001-x.md", out)
        self.assertNotIn("request 000001", out)
        self.assertIn("nothing new", self.ptt("inbox", d).stdout)
        self.assertIn("request 000001: new request 0001, waiting for review",
                      self.ptt("inbox", i).stdout)
        (req / "0002-review.md").write_text(f"---\nkind: review\nsession: {i}\n---\n")
        self.ptt("record", "-m", "pr 000001: review", str(req), session="I")
        self.assertNotIn("0002", self.ptt("inbox", i).stdout)
        quiet = self.ptt("inbox", "--quiet", session="W").stdout
        self.assertIn(f"ptt inbox for {w}", quiet)
        self.assertIn("request 000001: new review 0002", quiet)
        self.assertEqual(self.ptt("inbox", "--quiet", session="W").stdout, "")
        self.ptt("pr-move", "1", "merged", "-m", "pr 000001: merged", session="I")
        self.assertIn("request 000001: now merged", self.ptt("inbox", w).stdout)

    def test_inbox_tells_the_last_session_its_hold_ended(self):
        d = self.ptt("take", "designer", session="D").stdout.strip()
        a, b, c = (self.task(x, d) for x in ("a", "b", "c"))
        wa = self.ptt("take", a, session="A").stdout.strip()
        self.ptt("done", a, "--as", wa, session="A")
        self.ptt("close", a, "--as", d, session="D")
        quiet = self.ptt("inbox", "--quiet", session="A").stdout
        self.assertIn(f"T0001 was closed by {d} (records ", quiet)
        self.assertIn(f"{wa} holds nothing now; record nothing more as {wa}", quiet)
        self.assertEqual(self.ptt("inbox", "--quiet", session="A").stdout, "")
        self.assertIn(f"T0001 was closed by {d}; {wa} holds nothing now",
                      self.ptt("inbox", session="A").stdout)
        wb = self.ptt("take", b, session="B").stdout.strip()
        self.ptt("leave", wb, session="B")
        self.ptt("approve-leave", b, "--as", d, session="D")
        self.assertIn(f"{d} approved {wb}'s leaving T0002",
                      self.ptt("inbox", "--quiet", session="B").stdout)
        wc = self.ptt("take", c, session="C").stdout.strip()
        self.ptt("free", c, "--as", d, "--force", "--reason", "gone", session="D")
        self.assertIn(f"{wc} was freed from T0003 by {d}", self.ptt("inbox", wc).stdout)
        i = self.ptt("take", "integrator", session="I").stdout.strip()
        self.ptt("leave", i, session="I")               # its own leave: nothing to tell
        self.assertEqual(self.ptt("inbox", "--quiet", session="I").stdout, "")
        self.assertIn("this session holds nothing", self.ptt("inbox", session="X").stdout)

    def test_inbox_quiet_never_fails(self):
        self.assertEqual(self.ptt("inbox", "--quiet").stdout, "")
        shutil.rmtree(self.rec / ".git")
        r = self.ptt("inbox", "--quiet", session="X", check=False)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_unbound_holder_not_checked(self):
        d = self.ptt("take", "designer").stdout.strip()
        self.assertIn("not bound", self.ptt("take", "integrator").stderr)
        self.ptt("mktask", "x", "--as", d, session="B")
        self.ptt("resume", d, session="B")
        self.assertIn("bound to another session", self.refused(
            "mktask", "y", "--as", d, session="C"))
        self.assertTrue(list((self.rec / "tasks" / "open" / "T0000-design").glob("*-resume.md")))


if __name__ == "__main__":
    unittest.main()
