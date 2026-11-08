"""Tests for project/bin/ptt: roles, tasks, supervision, and concurrent claims,
in a temporary records repository.

Run: python3 -m unittest discover -s tests   (from the repository root)
"""
import json
import os
import re
import runpy
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# A calling Git (rebase --exec, a hook) exports variables such as GIT_DIR that
# would point the tests' git commands at its repository instead of theirs.
for _var in subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True,
                           text=True, check=True).stdout.split():
    os.environ.pop(_var, None)


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
        closed = self.ptt("close", "T0001", "--as", d)
        self.assertIn("A tasks/done/T0001-wall-distance/0004-close.md", closed.stderr)
        self.assertIn("R100 tasks/open/T0001-wall-distance/charter.md -> "
                      "tasks/done/T0001-wall-distance/charter.md", closed.stderr)
        self.assertIn("R100 tasks/open/T0001-wall-distance/status.md -> "
                      "tasks/done/T0001-wall-distance/status.md", closed.stderr)
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
        self.assertNotIn("note:", self.ptt("record", "-m", "submit", str(req2)).stderr)
        self.ptt("leave", "designer-g1")
        charter = self.rec / "tasks" / "open" / "T0000-design" / "charter.md"
        self.fill(charter)
        self.fill(charter.parent / "status.md")
        self.ptt("record", "-m", "fill", str(charter.parent))
        self.assertNotIn("note:", self.ptt("take", "designer", session="S").stderr)

    def test_record_and_pr_move_accept_as(self):
        req = self.rec / "pr" / "open" / "000001-x"
        req.mkdir(parents=True)
        (req / "0001-request.md").write_text("x\n")
        self.ptt("record", "-m", "pr 000001: submit", "--as", "track-T0001", str(req))
        run("git", "-C", str(self.rec), "config", "diff.renames", "false")
        moved = self.ptt("pr-move", "1", "merged", "-m", "pr 000001: merged", "--as", "integrator-1")
        self.assertRegex(moved.stderr, r"recorded [0-9a-f]+: R100 "
                         r"pr/open/000001-x/0001-request.md -> pr/merged/000001-x/0001-request.md\n")
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

    def test_adopt_clears_only_named_amendments_across_resume(self):
        d = self.designer()
        n = self.task("probe", d)
        holder = self.ptt("take", n, session="A").stdout.strip()
        for text in ("scope narrowed", "input clarified", "bounds specified"):
            self.ptt("amend", n, "--as", d, "--text", text)
        waiting = r"waits on you: amended since your take: (\d{4}-amend.md)"
        self.assertEqual(re.findall(waiting, self.ptt("inbox", holder).stdout),
                         ["0003-amend.md", "0004-amend.md", "0005-amend.md"])
        adopted = self.ptt("adopt", n, "3, 0005", "--as", holder,
                           "--text", "Updated the implementation and checks.", session="A")
        event = self.rec / "tasks" / "open" / "T0001-probe" / "0006-adopt.md"
        text = event.read_text()
        for field in (f"by: {holder}\n", "event: adopt\n", "amends: 0003, 0005\n",
                      "Updated the implementation and checks.\n"):
            self.assertIn(field, text)
        self.assertRegex(text, r"date: \d{4}-\d{2}-\d{2}\n")
        self.assertIn("A tasks/open/T0001-probe/0006-adopt.md", adopted.stderr)
        self.assertEqual(re.findall(waiting, self.ptt("inbox", holder).stdout), ["0004-amend.md"])
        self.ptt("resume", holder, session="B")
        self.assertEqual(re.findall(waiting, self.ptt("inbox", holder).stdout), ["0004-amend.md"])
        self.assertIn("continued in another session", self.refused(
            "adopt", n, "4", "--as", holder, session="A"))
        self.ptt("adopt", n, "4", "--as", holder, session="B")
        self.assertEqual(re.findall(waiting, self.ptt("inbox", holder).stdout), [])
        self.ptt("amend", n, "--as", d, "--text", "one more requirement")
        self.assertEqual(re.findall(waiting, self.ptt("inbox", holder).stdout), ["0009-amend.md"])
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

    def test_adopt_refuses_invalid_events_without_partial_writes(self):
        d = self.designer()
        n = self.task("probe", d)
        holder = self.ptt("take", n).stdout.strip()
        self.ptt("amend", n, "--as", d, "--text", "scope narrowed")
        before = run("git", "-C", str(self.rec), "rev-parse", "HEAD").stdout
        for numbers, actor, error in (("3", d, "does not hold"), ("3", "user", "does not hold"),
                                      ("9999", holder, "no event"), ("0", holder, "no event"),
                                      ("1", holder, "not an amendment"),
                                      ("2", holder, "not an amendment"),
                                      ("3,9999", holder, "no event"),
                                      ("3,2", holder, "not an amendment"),
                                      ("", holder, "event numbers"),
                                      ("3,", holder, "event numbers"),
                                      ("x", holder, "event numbers")):
            with self.subTest(numbers=numbers, actor=actor):
                self.assertIn(error, self.refused("adopt", n, numbers, "--as", actor))
                self.assertEqual(run("git", "-C", str(self.rec), "rev-parse", "HEAD").stdout, before)
                self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")
        self.ptt("adopt", n, "3,0003", "--as", holder)
        event = self.rec / "tasks" / "open" / "T0001-probe" / "0004-adopt.md"
        self.assertIn("\namends: 0003\n", event.read_text())
        self.ptt("amend", n, "--as", d, "--text", "input clarified")
        before = run("git", "-C", str(self.rec), "rev-parse", "HEAD").stdout
        for numbers in ("3", "5,3"):
            self.assertIn("already adopted", self.refused("adopt", n, numbers, "--as", holder))
            self.assertEqual(run("git", "-C", str(self.rec), "rev-parse", "HEAD").stdout, before)
            self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")
        self.assertIn("waits on you: amended since your take: 0005-amend.md",
                      self.ptt("inbox", holder).stdout)

    def test_designer_adopts_user_amendment_to_root_task(self):
        d = self.designer()
        self.ptt("amend", "T0000", "--as", "user", "--text", "design document moved")
        self.assertIn("waits on you: amended since your take: 0002-amend.md",
                      self.ptt("inbox", d).stdout)
        self.assertIn("does not hold", self.refused("adopt", "T0000", "2", "--as", "user"))
        self.ptt("adopt", "T0000", "2", "--as", d)
        event = self.rec / "tasks" / "open" / "T0000-design" / "0003-adopt.md"
        self.assertIn(f"by: {d}\n", event.read_text())
        self.assertNotIn("waits on you: amended", self.ptt("inbox", d).stdout)

    def test_writes_report_path_and_commit(self):
        """Every record names what it wrote and the records commit, on
        standard error; standard output stays what scripts read."""
        d = self.designer()
        n = self.task("probe", d)
        r = self.ptt("amend", n, "--as", d, "--text", "scope narrowed")
        head = run("git", "-C", str(self.rec), "rev-parse", "--short", "HEAD").stdout.strip()
        self.assertEqual(r.stderr, f"recorded {head}: A tasks/open/T0001-probe/0002-amend.md\n")
        holder = self.ptt("take", n)
        self.assertRegex(holder.stderr, r"recorded [0-9a-f]+: A tasks/open/T0001-probe/0003-take.md, "
                         r"A tasks/open/T0001-probe/status.md\n")
        self.assertEqual(holder.stdout.strip(), "track-T0001")

    def test_record_root_lists_committed_files(self):
        (self.rec / "a.md").write_text("my note\n")
        (self.rec / "b.md").write_text("another session's note\n")
        template = self.rec / "tasks" / "charter-template.md"
        template.write_text(template.read_text() + "\nAn update.\n")
        r = self.ptt("record", "-m", "record root", str(self.rec))
        head = run("git", "-C", str(self.rec), "rev-parse", "--short", "HEAD").stdout.strip()
        self.assertEqual(r.stderr, f"recorded {head}: A a.md, A b.md, M tasks/charter-template.md\n")
        self.assertEqual(r.stdout, "")
        unchanged = self.ptt("record", "-m", "unchanged", str(self.rec))
        self.assertEqual((unchanged.stdout, unchanged.stderr), ("nothing to record\n", ""))

    def test_record_directory_lists_only_changed_files(self):
        notes = self.rec / "notes"
        notes.mkdir()
        (notes / "a.md").write_text("before\n")
        (notes / "unchanged.md").write_text("same\n")
        self.ptt("record", "-m", "initial notes", str(notes))
        (notes / "a.md").write_text("after\n")
        (notes / "z.md").write_text("new\n")
        r = self.ptt("record", "-m", "updated notes", str(notes))
        head = run("git", "-C", str(self.rec), "rev-parse", "--short", "HEAD").stdout.strip()
        self.assertEqual(r.stderr, f"recorded {head}: M notes/a.md, A notes/z.md\n")

    def test_record_output_limit(self):
        for count, suffix in ((10, ""), (11, ", ... (11 files total)")):
            with self.subTest(count=count):
                notes = self.rec / f"batch{count}"
                notes.mkdir()
                for i in range(count):
                    (notes / f"{i:02d}.md").write_text(f"note {i}\n")
                r = self.ptt("record", "-m", "many notes", str(notes))
                head = run("git", "-C", str(self.rec), "rev-parse", "--short", "HEAD").stdout.strip()
                expected = ", ".join(f"A {notes.name}/{i:02d}.md" for i in range(10)) + suffix
                self.assertEqual(r.stderr, f"recorded {head}: {expected}\n")

    def test_first_record_lists_files(self):
        run("git", "-C", str(self.rec), "update-ref", "-d", "refs/heads/master")
        r = self.ptt("record", "-m", "first record", str(self.rec))
        head = run("git", "-C", str(self.rec), "rev-parse", "--short", "HEAD").stdout.strip()
        self.assertEqual(r.stderr, f"recorded {head}: A bin/ptt, A tasks/charter-template.md, "
                         "A tasks/open/T0000-design/charter.md\n")

    def test_record_report_failure_keeps_committed_files(self):
        ptt = runpy.run_path(str(self.rec / "bin" / "ptt"))
        git = ptt["git"]
        def fail_listing(*args, **kwargs):
            if args[0] == "diff-tree":
                raise SystemExit("listing failed")
            return git(*args, **kwargs)
        ptt["record"].__globals__["git"] = fail_listing
        note = self.rec / "note.md"
        note.write_text("keep this\n")
        with ptt["lock"](), self.assertRaisesRegex(SystemExit, "listing failed"):
            ptt["record"]("keep committed note", add=[note], created=[note])
        self.assertEqual(note.read_text(), "keep this\n")
        self.assertEqual(run("git", "-C", str(self.rec), "show", "HEAD:note.md").stdout, "keep this\n")
        self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain").stdout, "")

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

    def test_record_deletions(self):
        """A deletion is recorded after `rm` or after `git rm`; a path that is
        gone already, or never was, is refused and says which."""
        for name in ("a.md", "b.md"):
            (self.rec / name).write_text("x\n")
            self.ptt("record", "-m", f"add {name}", str(self.rec / name))
        (self.rec / "a.md").unlink()
        deleted = self.ptt("record", "-m", "delete a", str(self.rec / "a.md"))
        self.assertRegex(deleted.stderr, r"recorded [0-9a-f]+: D a.md\n")
        run("git", "-C", str(self.rec), "rm", "-q", "b.md")
        deleted = self.ptt("record", "-m", "delete b", str(self.rec / "b.md"))
        self.assertRegex(deleted.stderr, r"recorded [0-9a-f]+: D b.md\n")
        git = lambda *a: run("git", "-C", str(self.rec), *a).stdout
        self.assertEqual(git("ls-tree", "--name-only", "HEAD", "--", "a.md", "b.md"), "")
        self.assertEqual(git("status", "--porcelain"), "")
        gone = git("rev-parse", "--short", "HEAD").strip()
        r = self.ptt("record", "-m", "delete b again", str(self.rec / "b.md"),
                     check=False)
        self.assertIn(f"b.md is not in the records: already deleted (records {gone})", r.stderr)
        r = self.ptt("record", "-m", "typo", str(self.rec / "c.md"), check=False)
        self.assertIn("c.md is not in the records\n", r.stderr)

    def test_record_alongside_task_changes(self):
        d = self.designer()
        notes = self.rec / "notes.txt"
        script = ("for i in $(seq 40); do echo $i >> notes.txt; "
                  f"python3 {self.rec / 'bin' / 'ptt'} record -m n$i notes.txt >/dev/null; done")
        loop = subprocess.Popen(["sh", "-c", script], cwd=self.rec, stderr=subprocess.PIPE,
                                text=True)
        for k in range(12):
            self.ptt("mktask", f"s{k}", "--as", d)
        errors = [x for x in loop.communicate()[1].splitlines() if not x.startswith("recorded ")]
        self.assertEqual(errors, [])
        git = lambda *a: run("git", "-C", str(self.rec), *a).stdout
        tracked = git("ls-tree", "-r", "--name-only", "HEAD")
        for k in range(12):
            self.assertIn(f"tasks/open/T{k + 1:04d}-s{k}/charter.md", tracked)
        self.assertEqual(git("status", "--porcelain"), "")
        self.assertEqual(git("log", "-1", "--format=%s", "--", "notes.txt").strip(), "n40")
        self.assertEqual(loop.returncode, 0)

    def held_lock(self):
        """A ptt command holding the records lock: a pre-commit hook keeps it
        in `git commit` until killed."""
        hook = self.rec / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nsleep 60\n")
        hook.chmod(0o755)
        note = self.rec / "note.txt"
        note.write_text("x\n")
        proc = subprocess.Popen(["python3", str(self.rec / "bin" / "ptt"), "record", "-m",
                                 "held", str(note)], env=self.env(), start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        owner = self.rec / ".git" / "ptt.lock.d" / "owner"
        for _ in range(100):
            if owner.exists():
                break
            time.sleep(0.05)
        self.assertTrue(owner.exists())
        return proc, hook, owner

    def kill(self, proc, hook):
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        hook.unlink()
        (self.rec / ".git" / "index.lock").unlink(missing_ok=True)   # git's own, killed too
        run("git", "-C", str(self.rec), "reset", "-q")

    def test_lock_of_a_dead_process_is_removed(self):
        proc, hook, owner = self.held_lock()
        env = dict(self.env(), PTT_LOCK_WAIT="0.5")
        busy = run("python3", str(self.rec / "bin" / "ptt"), "take", "integrator",
                   env=env, check=False)
        self.assertIn("still running", busy.stderr)
        self.assertIn("which is running", self.refused("unlock"))
        self.kill(proc, hook)
        self.assertTrue(owner.exists())                 # left behind by the killed command
        r = self.ptt("take", "integrator")
        self.assertIn("removed a stale lock", r.stderr)
        self.assertFalse(owner.exists())

    def test_reused_process_number_does_not_keep_a_lock(self):
        proc, hook, owner = self.held_lock()
        self.kill(proc, hook)
        fields = owner.read_text().replace(f"pid={proc.pid}", f"pid={os.getpid()}")
        owner.write_text(re.sub(r"start=.*", "start=another process", fields))
        self.assertIn("removed the lock", self.ptt("unlock").stdout)
        self.assertIn("not locked", self.ptt("unlock").stdout)

    def test_lock_of_another_machine_is_removed_only_by_force(self):
        proc, hook, owner = self.held_lock()
        self.kill(proc, hook)
        owner.write_text(re.sub(r"machine=.*", "machine=elsewhere", owner.read_text()))
        env = dict(self.env(), PTT_LOCK_WAIT="0.3")
        r = run("python3", str(self.rec / "bin" / "ptt"), "take", "integrator",
                env=env, check=False)
        self.assertIn("another machine", r.stderr)
        self.assertIn("unlock --force", self.refused("unlock"))
        self.assertIn("removed the lock", self.ptt("unlock", "--force").stdout)
        self.ptt("take", "integrator")

    def test_broken_lock_is_removed_only_by_force(self):
        lock = self.rec / ".git" / "ptt.lock.d"
        # an empty one is replaced by the next command's lock; the others block it
        for name, text in (("", ""), ("stray", "x\n"),
                           ("owner", "host=h\nmachine=elsewhere\nsince=0\n"),
                           ("owner", "pid=1\n")):
            lock.mkdir()
            if name:
                (lock / name).write_text(text)
                env = dict(self.env(), PTT_LOCK_WAIT="0.3")
                r = run("python3", str(self.rec / "bin" / "ptt"), "take", "integrator",
                        env=env, check=False)
                self.assertIn("names no owner", r.stderr)
            self.assertIn("unlock --force", self.refused("unlock"))
            self.assertIn("removed the lock of no owner", self.ptt("unlock", "--force").stdout)
            self.assertFalse(lock.exists())
        self.ptt("take", "integrator")

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
        r = self.ptt("record", "-m", "a only", str(self.rec / "a.txt"))
        self.assertEqual(r.stdout, "")
        self.assertRegex(r.stderr, r"recorded [0-9a-f]+: A a.txt\n")
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
        # a new conversation has a new ID: writes as d are refused until resumed
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

    def test_hints_name_commands_in_the_calling_tools_notation(self):
        """`/ptt-...` in Claude Code, `$ptt-...` in Codex, both when the
        tool is unknown (PTT_SESSION_ID alone, or no session variable)."""
        claude, codex = "/{}", "${}"
        both = "/{0} in Claude Code, ${0} in Codex"
        for key, form in (("CLAUDE_CODE_SESSION_ID", claude), ("CODEX_THREAD_ID", codex),
                          ("CODEX_SESSION_ID", codex), ("PTT_SESSION_ID", both), (None, both)):
            with self.subTest(key=key):
                env_a = dict(self.env(), **({key: "A"} if key else {}))
                env_b = dict(self.env(), **({key: "B"} if key else {}))

                def native(*args, env=env_a, check=True):
                    return run("python3", str(self.rec / "bin" / "ptt"), *args,
                               env=env, check=check)

                holder = native("take", "integrator").stdout.strip()
                if key:
                    refusal = native("leave", holder, env=env_b, check=False).stderr
                    self.assertIn(f"continues {holder} in a new conversation, run "
                                  f"`ptt resume {holder}` first "
                                  f"({form.format(f'ptt-resume {holder}')})", refusal)
                    self.assertNotIn("/clear", refusal)
                handover = native("handover", holder).stdout
                self.assertIn(f"({form.format('ptt-resume')}) and no name", handover)
                native("leave", holder)

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

    def test_note_reaches_its_recipient_until_deleted(self):
        """A note goes to the role or task its `to:` names, not to its author;
        it waits on the recipient, also a later holder, until it is deleted."""
        d = self.ptt("take", "designer", session="D").stdout.strip()
        n = self.task("probe", d)
        w = self.ptt("take", n, session="W").stdout.strip()
        notes = self.rec / "handoff" / "notes"
        notes.mkdir(parents=True)
        (notes / "to-integrator.md").write_text("---\nto: integrator\n---\n\nmerge order\n")
        self.ptt("record", "-m", "note to the integrator", str(notes / "to-integrator.md"),
                 "--as", d, session="D")
        (notes / "to-task.md").write_text("---\nto: T0001\n---\n\nmind the bounds\n")
        self.ptt("record", "-m", "note to T0001", str(notes / "to-task.md"), "--as", d,
                 session="D")
        out = self.ptt("inbox", d).stdout
        self.assertNotIn("to-integrator", out)
        self.assertNotIn("to-task", out)
        out = self.ptt("inbox", w).stdout
        self.assertIn("read handoff/notes/to-task.md: a note to you", out)
        self.assertNotIn("to-integrator", out)
        i = self.ptt("take", "integrator", session="I").stdout.strip()
        out = self.ptt("inbox", i).stdout
        self.assertIn("waits on you: a note to you: handoff/notes/to-integrator.md", out)
        self.assertNotIn("to-task", out)
        (notes / "to-integrator.md").unlink()
        self.ptt("record", "-m", "note read", str(notes / "to-integrator.md"), "--as", i,
                 session="I")
        self.assertNotIn("to-integrator", self.ptt("inbox", i).stdout)

    def test_note_needs_a_recipient_in_front_matter(self):
        """Recording a note added or changed refuses one whose front matter
        names no role or open task, and records nothing; a deletion
        passes. A note written before the check, without `to:`, still goes
        to the designer, marked."""
        d = self.ptt("take", "designer", session="D").stdout.strip()
        n = self.task("probe", d)
        w = self.ptt("take", n, session="W").stdout.strip()
        done, cancelled = self.task("done", d), self.task("dropped", d)
        g = self.ptt("take", done, session="G").stdout.strip()
        self.ptt("done", done, "--as", g, session="G")
        self.ptt("close", done, "--as", d, session="D")
        self.ptt("cancel", cancelled, "--as", d, "--reason", "not needed", session="D")
        self.ptt("mktask", "draft", "--as", d)          # T0004, a draft: open, no holder
        notes = self.rec / "handoff" / "notes"
        notes.mkdir(parents=True)
        head = lambda: run("git", "-C", str(self.rec), "rev-parse", "HEAD").stdout
        header = "A note begins with front matter naming its recipient (designer, " \
                 "integrator, or an open task's ID such as T0007):\n---\nto: designer\n---\n"
        for text, why in (("bounds\n", "no front matter"),
                          ("to: T0001\n\nbounds\n", "a `to:` line outside front matter"),
                          ("---\nfrom: me\n---\n\nbounds\n", "front matter without `to:`"),
                          ("---\nto: T0099\n---\n\nbounds\n",
                           "`to: T0099` names neither designer, integrator, nor an open task"),
                          ("---\nto: wall-distance\n---\n\nbounds\n",
                           "`to: wall-distance` names neither designer, integrator, nor an "
                           "open task"),
                          ("---\nto: T0002\n---\n\nbounds\n",
                           "`to: T0002` names a task that is done, with no holder"),
                          ("---\nto: 3\n---\n\nbounds\n",
                           "`to: 3` names a task that is cancelled, with no holder")):
            (notes / "x.md").write_text(text)
            before = head()
            for target in (notes / "x.md", notes, self.rec):
                err = self.refused("record", "-m", "note", str(target), session="W")
                self.assertEqual(err, f"ptt: handoff/notes/x.md: {why}; nothing recorded. "
                                 + header, text)
                self.assertEqual(head(), before)
                self.assertEqual(run("git", "-C", str(self.rec), "status", "--porcelain",
                                     "--untracked-files=all").stdout, "?? handoff/notes/x.md\n")
        for to, who in (("designer", d), ("integrator", None), ("T0001", w), ("1", w),
                        ("t0000", d), ("T0004", None)):
            (notes / "x.md").write_text(f"---\nto: {to}\n---\n\nbounds\n")
            self.ptt("record", "-m", f"note to {to}", str(notes / "x.md"))
            for holder in (d, w):
                waits = "a note to you: handoff/notes/x.md;" in self.ptt("inbox", holder).stdout
                self.assertEqual(waits, holder == who, (to, holder))
        run("git", "-C", str(self.rec), "mv", str(notes / "x.md"), str(notes / "y.md"))
        self.assertIn("R100 handoff/notes/x.md -> handoff/notes/y.md",
                      self.ptt("record", "-m", "renamed", str(notes)).stderr)
        (notes / "x.md").write_text("changed without front matter\n")
        self.assertIn("no front matter", self.refused("record", "-m", "edit", str(notes / "x.md")))
        old = notes / "old.md"                          # written before the check
        old.write_text("to: T0001\n\nbounds\n")
        run("git", "-C", str(self.rec), "add", str(old))
        run("git", "-C", str(self.rec), "commit", "-qm", "old note")
        out = self.ptt("inbox", d).stdout
        mark = "; it names no recipient (no `to:` in front matter), so it is the designer's"
        self.assertIn(f"read handoff/notes/old.md: a note to you{mark} (", out)
        self.assertIn(f"waits on you: a note to you: handoff/notes/old.md{mark}; once read", out)
        self.assertNotIn("old.md", self.ptt("inbox", w).stdout)
        old.unlink()
        r = self.ptt("record", "-m", "old note read", str(old), session="D")
        self.assertIn("D handoff/notes/old.md", r.stderr)

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
        note.write_text("---\nto: designer\n---\n\nx\n")
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

    def test_handover_lets_a_fresh_session_resume_without_a_name(self):
        i = self.ptt("take", "integrator", session="A").stdout.strip()
        self.assertIn("only that session", self.refused("handover", i, session="X"))
        self.ptt("handover", i, session="A")
        r = self.ptt("resume", session="B")
        self.assertIn(f"{i} left a handover", r.stdout)
        self.assertIn(f"this session is {i}", r.stdout)
        self.assertFalse((self.rec / ".git" / "ptt-handover" / i).exists())
        # the old session is told once, and its writes are refused
        quiet = self.ptt("inbox", "--quiet", session="A").stdout
        self.assertIn(f"{i} continues in another session", quiet)
        self.assertEqual(self.ptt("inbox", "--quiet", session="A").stdout, "")
        self.assertIn("continued in another session", self.refused("leave", i, session="A"))

    def test_handover_lapses_when_its_holder_writes_again(self):
        i = self.ptt("take", "integrator", session="A").stdout.strip()
        d = self.ptt("take", "designer", session="D").stdout.strip()
        self.ptt("handover", i, session="A")
        status = self.rec / "handoff" / "integrator.md"
        status.parent.mkdir(exist_ok=True)
        status.write_text("still here\n")
        self.ptt("record", "-m", "integrator: status", str(status), session="A")
        self.assertIn(f"(by {i})", run("git", "-C", str(self.rec), "log", "-1",
                                       "--format=%s").stdout)
        menu = self.ptt("resume", session="B").stdout
        self.assertIn("Which holder", menu)
        self.assertNotIn("handover left", menu)
        self.assertRegex(menu, rf"{i} +last write just now; may still be working")
        self.assertIn(d, menu)
        self.assertNotIn("this session is", menu)
        self.assertFalse((self.rec / ".git" / "ptt-handover" / i).exists())

    def test_resume_lists_two_handovers_instead_of_choosing(self):
        i = self.ptt("take", "integrator", session="A").stdout.strip()
        d = self.ptt("take", "designer", session="D").stdout.strip()
        self.ptt("handover", i, session="A")
        self.ptt("handover", d, session="D")
        menu = self.ptt("resume", session="B").stdout
        self.assertRegex(menu, rf"1\. ({i}|{d}) +handover left")
        self.assertRegex(menu, rf"2\. ({i}|{d}) +handover left")
        self.assertIn(f"this session is {d}", self.ptt("resume", d, session="B").stdout)
        self.assertIn(f"{i} left a handover", self.ptt("resume", session="C").stdout)

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

    def test_session_name_codes(self):
        ptt = runpy.run_path(str(self.rec / "bin" / "ptt"))
        for word, code in (("Partitur", "prtr"), ("Fynamiq", "fnmq"), ("Wobbleggs", "wblg"),
                           ("iConverge", "icnv"), ("abc", "abc"), ("Ab-c", "abc"),
                           ("worker", "wrkr"), ("track", "trck"), ("design", "dsgn")):
            self.assertEqual(ptt["short_code"](word), code, word)
        for holder, code in (("designer-g1", "dsgn-g1"), ("integrator-1", "intg-1"),
                             ("worker-T0008", "wrkr-t8"), ("worker-T0008-2", "wrkr-t8-2"),
                             ("track-T0007.1", "trck-t7.1"), ("design-T0012-3", "dsgn-t12-3")):
            self.assertEqual(ptt["holder_code"](holder), code, holder)
        self.assertEqual(ptt["project_code"](), ptt["short_code"](self.root.name))
        (self.rec / "project-code").write_text("Mine\n")
        self.assertEqual(ptt["project_code"](), "mine")
        (self.rec / "project-code").write_text("my code\n")
        with self.assertRaises(SystemExit):
            ptt["project_code"]()

    def test_session_name_hash_windows(self):
        windows = runpy.run_path(str(self.rec / "bin" / "ptt"))["hash_windows"]
        v4 = windows("d28136ab-07f9-4957-bb62-fc56522ba145")
        self.assertEqual(v4[:8], ["2ba145", "22ba14", "522ba1", "6522ba", "56522b", "c56522",
                                  "fc5652", "22ba145"])
        self.assertEqual(v4[-1], "fc56522ba145")
        v7 = windows("01A1A3DB-A88F-7251-8000-0123456789AB")
        self.assertEqual(v7[:2], ["6789ab", "56789a"])
        self.assertEqual(windows("thread:42-Abcdefghijklm")[:2], ["hijklm", "ghijkl"])
        self.assertEqual(windows("A"), ["a"])

    def test_session_name_recorded_once_and_moves_on_collision(self):
        (self.rec / "project-code").write_text("prtr\n")
        a = "00000000-0000-4000-8000-111111123456"
        b = "00000000-0000-4000-8000-222222123456"
        r = self.ptt("take", "designer", session=a)
        self.assertEqual(r.stdout, "designer-g1\n")
        self.assertIn("session name: prtr-dsgn-g1-123456\n", r.stderr)
        take = self.rec / "tasks" / "open" / "T0000-design" / "0001-take.md"
        self.assertIn("\nsession_name: prtr-dsgn-g1-123456\n", take.read_text())
        # another session of the same holder with the same last six digits
        r = self.ptt("resume", "designer-g1", session=b)
        self.assertIn("session name: prtr-dsgn-g1-212345\n", r.stderr)
        # the first session's own earlier name is not a collision
        r = self.ptt("resume", "designer-g1", session=a)
        self.assertIn("session name: prtr-dsgn-g1-123456\n", r.stderr)
        n = self.task("probe", "designer-g1", kind="worker")
        self.ptt("take", n, session="00000000-0000-4000-8000-333333123456")
        self.ptt("take", "integrator", session="00000000-0000-4000-8000-444444abcdef")
        who = self.ptt("who").stdout
        self.assertIn("designer    designer-g1  session prtr-dsgn-g1-123456  unseen", who)
        self.assertIn("integrator  integrator-1  session prtr-intg-1-abcdef  unseen", who)
        self.assertIn("worker-T0001  (worker, probe)  session prtr-wrkr-t1-123456  unseen", who)
        me = self.ptt("whoami", session=a).stdout
        self.assertIn("session: this one\nsession name: prtr-dsgn-g1-123456\n", me)
        self.assertIn("In Claude Code, so that automatic messages reach this session, rename it: "
                      "/rename prtr-dsgn-g1-123456; in Codex, to show it, type: /rename, then "
                      "enter prtr-dsgn-g1-123456\n", me)
        other = self.ptt("whoami", "designer-g1", session=b).stdout
        self.assertIn("session name: prtr-dsgn-g1-123456\n", other)
        self.assertNotIn("/rename", other)
        # no session ID: no name
        self.ptt("leave", "integrator-1")
        r = self.ptt("take", "integrator")
        self.assertNotIn("session name", r.stderr)
        self.assertEqual(self.ptt("who").stdout.splitlines()[1],
                         "integrator  integrator-2  unseen none")

    def test_who_shows_unseen_items_since_the_inbox_mark(self):
        d = self.ptt("take", "designer", session="D").stdout.strip()
        n = self.task("probe", d)
        w = self.ptt("take", n, session="W").stdout.strip()
        # never looked: counted from its take (the worker's status.md is new to d)
        who = self.ptt("who").stdout
        self.assertRegex(who, rf"designer    {d}  session \S+  unseen 1, oldest (just now|\d+ min ago)\n")
        self.assertIn(f"{w}  (track, probe)  session", who)
        self.assertRegex(who, rf"{w} .*  unseen none\n")
        # looking moves the mark; a later item is unseen again
        self.ptt("inbox", d, session="D")
        self.assertRegex(self.ptt("who").stdout, rf"designer    {d} .*  unseen none\n")
        self.ptt("amend", n, "--as", d, "--text", "more", session="D")
        self.ptt("amend", n, "--as", d, "--text", "and more", session="D")
        self.assertRegex(self.ptt("who").stdout, rf"{w} .*  unseen 2, oldest ")
        # a prompt hook's quiet inbox counts as seen
        self.ptt("inbox", w, "--quiet", session="W")
        self.assertRegex(self.ptt("who").stdout, rf"{w} .*  unseen none\n")

    def test_resume_names_a_session_bound_before_names(self):
        (self.rec / "project-code").write_text("prtr\n")
        sid = "00000000-0000-4000-8000-aaaaaa123456"
        self.ptt("take", "integrator", session=sid)
        # as a release before session names recorded it
        take = self.rec / "roles" / "integrator" / "0001-take.md"
        take.write_text(take.read_text().replace("session_name: prtr-intg-1-123456\n", ""))
        run("git", "-C", str(self.rec), "commit", "-qam", "old take")
        self.assertNotIn("session prtr", self.ptt("who").stdout)
        r = self.ptt("resume", "integrator-1", session=sid)
        self.assertIn("this session is already integrator-1", r.stdout)
        self.assertIn("session name: prtr-intg-1-123456\n", r.stderr)
        resume = self.rec / "roles" / "integrator" / "0002-resume.md"
        self.assertIn("\nsession_name: prtr-intg-1-123456\n", resume.read_text())
        self.assertIn("integrator-1  session prtr-intg-1-123456", self.ptt("who").stdout)
        # already named: printed again, nothing recorded
        r = self.ptt("resume", "integrator-1", session=sid)
        self.assertIn("session name: prtr-intg-1-123456\n", r.stderr)
        self.assertFalse((self.rec / "roles" / "integrator" / "0003-resume.md").exists())
        self.ptt("leave", "integrator-1", session=sid)

    def test_nudge_targets_per_event_kind(self):
        (self.rec / "project-code").write_text("prtr\n")
        sd, sw, si = (f"00000000-0000-4000-8000-0000000{x}" for x in ("0d0d0", "0eeee", "0abcd"))
        d = self.ptt("take", "designer", session=sd).stdout.strip()
        n = self.task("probe", d)
        w = self.ptt("take", n, session=sw).stdout.strip()
        i = self.ptt("take", "integrator", session=si).stdout.strip()
        names = {d: "prtr-dsgn-g1-00d0d0", w: "prtr-trck-t1-00eeee", i: "prtr-intg-1-00abcd"}

        def nudged(r):
            found = re.findall(r"^nudge: (\S+): new in your inbox \(records [0-9a-f]+\); run "
                               r"`workspace/bin/ptt inbox (\S+)`$", r.stderr, re.M)
            if found:
                self.assertIn("\nnudges: in Claude Code, for each session above that ListAgents "
                              "lists, subscribe with SendMessage notify_when_idle", r.stderr)
            for session, holder in found:
                self.assertEqual(session, names[holder])
            return [holder for _, holder in found]
        # an amendment, to the holder; never to the writer
        self.assertEqual(nudged(self.ptt("amend", n, "--as", d, "--text", "x", session=sd)), [w])
        # a subordinate's status update: none
        status = self.rec / "tasks" / "open" / "T0001-probe" / "status.md"
        status.write_text("progress\n")
        self.assertEqual(nudged(self.ptt("record", "-m", "s", str(status), session=sw)), [])
        # a note, to its recipient
        notes = self.rec / "handoff" / "notes"
        notes.mkdir(parents=True)
        (notes / "f.md").write_text("---\nto: designer\n---\n\nA finding.\n")
        self.assertEqual(nudged(self.ptt("record", "-m", "n", str(notes / "f.md"), session=sw)), [d])
        # a new request, to the integrator; a review, to the requester
        pr = self.rec / "pr" / "open" / "000001-probe"
        pr.mkdir(parents=True)
        (pr / "0001-request.md").write_text(f"---\nkind: request\nsession: {w}\n---\n")
        self.assertEqual(nudged(self.ptt("record", "-m", "pr", str(pr), session=sw)), [i])
        (pr / "0002-review.md").write_text(f"---\nkind: review\nsession: {i}\n---\n")
        self.assertEqual(nudged(self.ptt("record", "-m", "rv", str(pr / "0002-review.md"),
                                         session=si)), [w])
        # switched off: no targets, nothing lost; `who` shows the switch
        self.assertEqual(self.ptt("nudges").stdout, "nudges on\n")
        self.assertEqual(self.ptt("nudges", "off").stdout, "nudges off\n")
        r = self.ptt("amend", n, "--as", d, "--text", "y", session=sd)
        self.assertNotIn("nudge", r.stderr)
        who = self.ptt("who").stdout
        self.assertEqual(who.splitlines()[0], "nudges      off")
        self.assertRegex(who, rf"{w} .*  unseen 3, ")
        self.assertEqual(self.ptt("nudges", "on").stdout, "nudges on\n")
        self.assertEqual(self.ptt("who").stdout.splitlines()[0], "nudges      on")
        # a done report, to the supervisor; a request moved, to its requester
        self.assertEqual(nudged(self.ptt("done", n, "--as", w, session=sw)), [d])
        self.assertEqual(nudged(self.ptt("pr-move", "1", "merged", "-m", "m", session=si)), [w])
        # a close, to the former holder
        self.assertEqual(nudged(self.ptt("close", n, "--as", d, session=sd)), [w])
        # a holder without a recorded session name gets no line
        self.ptt("leave", i, session=si)
        self.ptt("take", "integrator")
        (notes / "g.md").write_text("---\nto: integrator\n---\n\nLate.\n")
        r = self.ptt("record", "-m", "n", str(notes / "g.md"), session=sd)
        self.assertNotIn("nudge", r.stderr)

    def test_rename_line_in_the_calling_tools_notation(self):
        (self.rec / "project-code").write_text("prtr\n")
        for key, line in (("CLAUDE_CODE_SESSION_ID", "So that automatic messages reach this "
                           "session, rename it: /rename prtr-intg-{n}-abcdef\n"),
                          ("CODEX_THREAD_ID", "to show it, type: /rename, then enter "
                           "prtr-intg-{n}-abcdef\n")):
            with self.subTest(key=key):
                env = dict(self.env(), **{key: f"0-0-0-0-{key[:2].lower()}00abcdef"})
                r = run("python3", str(self.rec / "bin" / "ptt"), "take", "integrator", env=env)
                n = r.stdout.strip().rsplit("-", 1)[1]
                self.assertIn("\n" + line.format(n=n), r.stderr)
                run("python3", str(self.rec / "bin" / "ptt"), "leave", f"integrator-{n}",
                    env=env)


if __name__ == "__main__":
    unittest.main()
