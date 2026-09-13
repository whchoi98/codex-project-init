"""Standalone skill installation against isolated profiles and real files."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts import install as installer
from scripts import skill_install as skill_installer


ROOT = Path(__file__).resolve().parents[1]


def snapshot(root, *, strict=False):
    """Capture bytes and links without following links or opening special files."""
    result = {}

    def visit(path):
        info = path.lstat()
        relative = path.relative_to(root).as_posix()
        if stat.S_ISLNK(info.st_mode):
            value = ("link", os.readlink(path))
        elif stat.S_ISREG(info.st_mode):
            value = ("file", path.read_bytes(), stat.S_IMODE(info.st_mode))
        elif stat.S_ISDIR(info.st_mode):
            value = ("directory", stat.S_IMODE(info.st_mode))
        else:
            value = ("special", info.st_mode)
        if strict:
            value += (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns)
        result[relative] = value
        if stat.S_ISDIR(info.st_mode):
            for child in sorted(path.iterdir()):
                visit(child)

    if os.path.lexists(root):
        visit(root)
    return result


def file_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


class SkillInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-init-skill-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        shutil.copytree(
            ROOT, self.source,
            ignore=shutil.ignore_patterns(
                ".git", ".codex", "dist", "__pycache__", "tests",
            ),
        )
        # The checkout's catalogue directories may be mounted read-only. Only
        # this owned copy needs writable ancestors for a self-project install.
        copied_agents = self.source / ".agents"
        if copied_agents.is_dir():
            for path in [copied_agents] + list(copied_agents.rglob("*")):
                if path.is_dir():
                    path.chmod(stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)
        self.skill = self.source / "skills/project-init"
        self.home = self.root / "home"
        self.codex_home = self.root / "unavailable-codex"
        self.destination = self.home / ".agents/skills/project-init"
        self.environment = {
            "HOME": str(self.home),
            "CODEX_HOME": str(self.codex_home),
            "PATH": str(self.root / "no-executables"),
        }

    def run_installer(self, *args):
        # No -B or PYTHONDONTWRITEBYTECODE: the installer must suppress its
        # own import caches. -S also excludes optional site dependencies.
        return subprocess.run(
            [sys.executable, "-S", str(self.source / "scripts/install.py"), *args],
            env=self.environment, cwd=self.root, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=30,
        )

    def assert_rejected_without_writes(self, *args, code=1):
        before = snapshot(self.root, strict=True)
        completed = self.run_installer(*args)
        self.assertEqual(completed.returncode, code, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotIn("PRIVATE_FIXTURE", completed.stderr)
        self.assertEqual(snapshot(self.root, strict=True), before)
        return completed

    def seed_destination(self):
        self.destination.mkdir(parents=True)
        (self.destination / "user-notes.txt").write_text("retain previous skill")
        (self.destination / "nested").mkdir()
        (self.destination / "nested/old.bin").write_bytes(b"\x00previous\xff")
        return snapshot(self.destination)

    def plan(self, **kwargs):
        return skill_installer.build_plan(
            source=self.source, home=self.home, environment=self.environment, **kwargs,
        )

    def assert_backup_retained(self, error, previous):
        backups = [
            path.parent for path in self.destination.parent.rglob("user-notes.txt")
            if path.parent != self.destination
        ]
        self.assertEqual(len(backups), 1)
        self.assertEqual(snapshot(backups[0]), previous)
        self.assertIn(str(backups[0]), str(error))
        self.assertNotIn("restored", str(error).lower())
        self.assertNotIn("PRIVATE_FIXTURE", str(error))

    def operation_path(self, path, descriptor=None):
        """Locate a fault-injection operand inside this owned fixture."""
        path = Path(path)
        if descriptor is None or path.is_absolute():
            return path
        info = os.fstat(descriptor)
        for directory, _dirs, _files in os.walk(self.root, followlinks=False):
            candidate = Path(directory)
            current = candidate.lstat()
            if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
                return candidate / path
        self.fail("Fault-injection descriptor is outside the fixture.")

    @contextmanager
    def intercept_rename(self, callback):
        # Keep the same real-filesystem fault scenarios across the transition
        # from path-based replace() to descriptor-relative rename().
        with mock.patch.object(skill_installer.os, "replace", callback), \
                mock.patch.object(skill_installer.os, "rename", callback):
            yield

    def test_user_install_succeeds_without_codex_or_helpers(self):
        expected = file_bytes(self.skill)
        before = snapshot(self.source, strict=True)
        completed = self.run_installer("--mode", "skill")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["mode"], "skill")
        self.assertEqual(report["scope"], "user")
        self.assertEqual(report["destination"], str(self.destination))
        self.assertIsNone(report["backup"])
        self.assertEqual(file_bytes(self.destination), expected)
        self.assertEqual(snapshot(self.source, strict=True), before)
        self.assertFalse(self.codex_home.exists())
        self.assertFalse((self.home / ".agents/plugins").exists())
        self.assertFalse((self.home / "plugins").exists())

    def test_project_install_preserves_user_profile_and_unrelated_skills(self):
        project = self.root / "project with spaces"
        other = project / ".agents/skills/other-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("retain project skill")
        user_skill = self.home / ".agents/skills/other-skill"
        user_skill.mkdir(parents=True)
        (user_skill / "SKILL.md").write_text("retain user skill")
        before_home = snapshot(self.home, strict=True)
        before_other = snapshot(other, strict=True)
        completed = self.run_installer("--mode", "skill", "--project", str(project))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        destination = project / ".agents/skills/project-init"
        self.assertEqual(report["scope"], "project")
        self.assertEqual(report["project"], str(project))
        self.assertEqual(report["destination"], str(destination))
        self.assertEqual(file_bytes(destination), file_bytes(self.skill))
        self.assertEqual(snapshot(self.home, strict=True), before_home)
        self.assertEqual(snapshot(other, strict=True), before_other)

    def test_dry_run_leaves_source_and_missing_destination_parents_unchanged(self):
        project = self.root / "project"
        project.mkdir()
        for extra, destination in (
            ((), self.destination),
            (("--project", str(project)), project / ".agents/skills/project-init"),
        ):
            with self.subTest(scope="project" if extra else "user"):
                before = snapshot(self.root, strict=True)
                completed = self.run_installer("--mode", "skill", "--dry-run", *extra)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(completed.stdout)
                self.assertEqual(report["destination"], str(destination))
                self.assertFalse(report["replace_existing_source"])
                self.assertEqual(snapshot(self.root, strict=True), before)

    def test_dry_run_replacement_does_not_touch_existing_install_or_parent(self):
        self.seed_destination()
        before = snapshot(self.root, strict=True)
        completed = self.run_installer("--mode", "skill", "--dry-run", "--replace")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["replace_existing_source"])
        self.assertEqual(snapshot(self.root, strict=True), before)

    def test_skill_install_does_not_read_or_change_marketplace_or_codex_config(self):
        marketplace = self.home / ".agents/plugins/marketplace.json"
        marketplace.parent.mkdir(parents=True)
        marketplace.write_text("PRIVATE_FIXTURE deliberately not marketplace JSON")
        self.codex_home.mkdir()
        (self.codex_home / "config.toml").write_text("PRIVATE_FIXTURE opaque config")
        other = self.home / ".agents/skills/other-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("retain")
        preserved = (marketplace, self.codex_home, other)
        before = [snapshot(path, strict=True) for path in preserved]
        completed = self.run_installer("--mode", "skill")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            [snapshot(path, strict=True) for path in preserved], before,
        )
        self.assertNotIn("PRIVATE_FIXTURE", completed.stdout + completed.stderr)

    def test_full_skill_payload_keeps_nested_resources_and_excludes_caches(self):
        resource = self.skill / "resources/nested/example.bin"
        resource.parent.mkdir(parents=True)
        resource.write_bytes(b"\x00resource\xff\n")
        expected = file_bytes(self.skill)
        for relative in (
            "__pycache__/cached.pyc", "node_modules/vendor/index.js",
            ".hidden", ".env", "references/secrets.json", "resources/draft.tmp",
        ):
            path = self.skill / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE_FIXTURE excluded")
        (self.source / "unrelated.txt").write_text("outside skill")
        other_skill = self.source / "skills/other/SKILL.md"
        other_skill.parent.mkdir()
        other_skill.write_text("outside selected skill")
        before = snapshot(self.source, strict=True)
        completed = self.run_installer("--mode", "skill")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(file_bytes(self.destination), expected)
        self.assertEqual(snapshot(self.source, strict=True), before)
        self.assertNotIn("PRIVATE_FIXTURE", completed.stdout + completed.stderr)

    def test_installation_does_not_execute_skill_or_project_scripts(self):
        marker = self.root / "script-was-executed"
        executable_contents = (
            "from pathlib import Path\n"
            "Path(" + repr(str(marker)) + ").write_text('unexpected execution')\n"
        )
        (self.skill / "scripts/install_probe.py").write_text(executable_contents)
        project = self.root / "project"
        project.mkdir()
        (project / "setup.py").write_text(executable_contents)
        completed = self.run_installer("--mode", "skill", "--project", str(project))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(
            (project / ".agents/skills/project-init/scripts/install_probe.py").read_text(),
            executable_contents,
        )

    def test_existing_destination_requires_explicit_replace(self):
        self.seed_destination()
        for extra in ((), ("--dry-run",)):
            with self.subTest(dry_run=bool(extra)):
                completed = self.assert_rejected_without_writes("--mode", "skill", *extra)
                self.assertIn("--replace", completed.stderr)

    def test_plugin_only_and_project_only_arguments_are_usage_errors(self):
        for args, rejected in (
            (("--mode", "skill", "--codex", "/unused/codex"), "--codex"),
            (("--mode", "skill", "--codex", ""), "--codex"),
            (("--project", str(self.root)), "--project"),
            (("--mode", "plugin", "--project", str(self.root)), "--project"),
        ):
            with self.subTest(args=args):
                completed = self.assert_rejected_without_writes(*args, code=2)
                self.assertIn(rejected, completed.stderr)
                self.assertIn("only", completed.stderr)
        self.assert_rejected_without_writes("--mode", "unknown", code=2)

    def test_project_scope_requires_an_existing_real_directory(self):
        regular = self.root / "project-file"
        regular.write_text("retain")
        linked = self.root / "project-link"
        linked.symlink_to(self.source, target_is_directory=True)
        dangling = self.root / "project-dangling"
        dangling.symlink_to(self.root / "absent")
        for project in (self.root / "missing", regular, linked, dangling):
            with self.subTest(project=project.name):
                self.assert_rejected_without_writes(
                    "--mode", "skill", "--project", str(project),
                )

    def test_unsafe_destination_types_and_ancestors_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("PRIVATE_FIXTURE retain")
        for kind in ("file", "fifo", "link", "dangling", "agents-link", "skills-link"):
            with self.subTest(kind=kind):
                project = self.root / ("project-" + kind)
                project.mkdir()
                destination = project / ".agents/skills/project-init"
                if kind == "agents-link":
                    (project / ".agents").symlink_to(outside, target_is_directory=True)
                elif kind == "skills-link":
                    (project / ".agents").mkdir()
                    (project / ".agents/skills").symlink_to(outside, target_is_directory=True)
                else:
                    destination.parent.mkdir(parents=True)
                    if kind == "file":
                        destination.write_text("retain")
                    elif kind == "fifo":
                        os.mkfifo(destination)
                    else:
                        destination.symlink_to(
                            outside if kind == "link" else self.root / "absent",
                            target_is_directory=True,
                        )
                self.assert_rejected_without_writes(
                    "--mode", "skill", "--project", str(project), "--replace",
                )

    def test_user_scope_rejects_linked_home_and_root_home(self):
        linked_home = self.root / "linked-home"
        linked_home.symlink_to(self.source, target_is_directory=True)
        for home in (linked_home, Path(self.root.anchor)):
            with self.subTest(home=str(home)):
                self.environment["HOME"] = str(home)
                self.assert_rejected_without_writes("--mode", "skill", "--dry-run")

    def test_destination_must_not_overlap_the_source_skill(self):
        self.assert_rejected_without_writes(
            "--mode", "skill", "--project", str(self.skill), "--replace",
        )
        self.destination.parent.mkdir(parents=True)
        self.source.rename(self.destination)
        self.source = self.destination
        self.assert_rejected_without_writes("--mode", "skill", "--replace")
        nested_source = self.destination / "checkout"
        self.source.rename(self.root / "moved-source")
        self.destination.mkdir()
        (self.root / "moved-source").rename(nested_source)
        self.source = nested_source
        self.assert_rejected_without_writes("--mode", "skill", "--replace")

    def test_checkout_can_receive_a_project_skill_outside_the_payload(self):
        expected = file_bytes(self.skill)
        before_skill = snapshot(self.skill, strict=True)
        before_source = file_bytes(self.source)
        completed = self.run_installer("--mode", "skill", "--project", str(self.source))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        destination = self.source / ".agents/skills/project-init"
        self.assertEqual(file_bytes(destination), expected)
        self.assertEqual(snapshot(self.skill, strict=True), before_skill)
        self.assertEqual(
            {name: data for name, data in file_bytes(self.source).items()
             if not name.startswith(".agents/skills/")},
            before_source,
        )

    def test_invalid_or_linked_source_payload_fails_before_publication(self):
        outside = self.root / "outside.txt"
        outside.write_text("PRIVATE_FIXTURE outside")
        linked = self.skill / "references/linked.txt"
        linked.symlink_to(outside)
        self.assert_rejected_without_writes("--mode", "skill")
        linked.unlink()
        os.mkfifo(linked)
        self.assert_rejected_without_writes("--mode", "skill")
        linked.unlink()
        (self.skill / "scripts/project_init_audit/git.py").unlink()
        self.assert_rejected_without_writes("--mode", "skill")

    def test_replace_keeps_an_exact_backup_and_preserves_previous_backups(self):
        previous = self.seed_destination()
        expected = file_bytes(self.skill)
        source_before = snapshot(self.source, strict=True)
        completed = self.run_installer("--mode", "skill", "--replace")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        backup = Path(report["backup"])
        self.assertNotEqual(backup, self.destination)
        self.assertEqual(snapshot(backup), previous)
        self.assertEqual(file_bytes(self.destination), expected)
        self.assertEqual(snapshot(self.source, strict=True), source_before)
        self.assertEqual(
            report["installed_version"],
            json.loads((self.source / ".codex-plugin/plugin.json").read_text())["version"],
        )
        backup_before = snapshot(backup, strict=True)
        replaced = self.run_installer("--mode", "skill", "--replace")
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        next_backup = Path(json.loads(replaced.stdout)["backup"])
        self.assertNotEqual(next_backup, backup)
        self.assertEqual(file_bytes(next_backup), expected)
        self.assertEqual(snapshot(backup, strict=True), backup_before)

    def test_preflight_does_not_change_process_or_supplied_environment(self):
        process_before = dict(os.environ)
        supplied_before = dict(self.environment)
        self.plan()
        self.assertEqual(dict(os.environ), process_before)
        self.assertEqual(self.environment, supplied_before)
        self.assertFalse(self.home.exists())

    def test_publication_uses_validated_bytes_even_when_source_disappears(self):
        expected = file_bytes(self.skill)
        plan = self.plan()
        shutil.rmtree(self.skill)
        skill_installer.install(plan)
        self.assertEqual(file_bytes(self.destination), expected)

    def test_candidate_write_failure_does_not_move_the_old_directory(self):
        self.seed_destination()
        before = snapshot(self.destination, strict=True)
        plan = self.plan(replace=True)
        real_open = Path.open
        real_os_open = os.open

        def fail_candidate_write(path, mode="r", *args, **kwargs):
            if ("x" in mode or "w" in mode) and path.name == "SKILL.md":
                raise OSError("PRIVATE_FIXTURE candidate write failed")
            return real_open(path, mode, *args, **kwargs)

        def fail_candidate_open(path, flags, mode=0o777, *, dir_fd=None):
            if flags & os.O_CREAT and Path(path).name == "SKILL.md":
                raise OSError("PRIVATE_FIXTURE candidate write failed")
            return real_os_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(Path, "open", fail_candidate_write), \
                mock.patch.object(skill_installer.os, "open", fail_candidate_open):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertEqual(snapshot(self.destination, strict=True), before)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])
        self.assertNotIn("PRIVATE_FIXTURE", str(raised.exception))

    def test_failed_first_publication_leaves_no_partial_skill(self):
        plan = self.plan()

        with self.intercept_rename(mock.Mock(side_effect=OSError("PRIVATE_FIXTURE"))):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [])
        self.assertNotIn("PRIVATE_FIXTURE", str(raised.exception))

    def test_failed_publication_restores_the_previous_directory(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        real_replace = os.replace

        def fail_publication(source, destination, **kwargs):
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if destination_path == self.destination and (source_path / "SKILL.md").is_file():
                raise OSError("PRIVATE_FIXTURE publication failed")
            return real_replace(source, destination, **kwargs)

        with self.intercept_rename(fail_publication):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])
        self.assertIn("restored", str(raised.exception).lower())
        self.assertNotIn("PRIVATE_FIXTURE", str(raised.exception))

    def test_error_after_candidate_rename_still_restores_the_old_directory(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        real_replace = os.replace

        def interrupt_after_publication(source, destination, **kwargs):
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            candidate = (source_path / "SKILL.md").is_file()
            result = real_replace(source, destination, **kwargs)
            if destination_path == self.destination and candidate:
                raise KeyboardInterrupt
            return result

        with self.intercept_rename(interrupt_after_publication):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertIn("restored", str(raised.exception).lower())

    def test_error_after_backup_rename_still_restores_the_old_directory(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        real_replace = os.replace

        def interrupt_after_backup(source, destination, **kwargs):
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            result = real_replace(source, destination, **kwargs)
            if source_path == self.destination:
                raise KeyboardInterrupt
            return result

        with self.intercept_rename(interrupt_after_backup):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertIn("restored", str(raised.exception).lower())

    def test_recovery_failure_retains_and_reports_the_backup(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        real_replace = os.replace

        def fail_publication_and_recovery(source, destination, **kwargs):
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if destination_path == self.destination:
                raise OSError("PRIVATE_FIXTURE cannot publish or restore")
            return real_replace(source, destination, **kwargs)

        with self.intercept_rename(fail_publication_and_recovery):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertFalse(self.destination.exists())
        self.assert_backup_retained(raised.exception, previous)

    def test_unexpected_directory_at_publication_is_not_deleted_by_recovery(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        real_replace = os.replace

        def concurrent_destination(source, destination, **kwargs):
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if destination_path == self.destination and (source_path / "SKILL.md").is_file():
                self.destination.mkdir()
                (self.destination / "concurrent.txt").write_text("retain concurrent install")
                raise OSError("PRIVATE_FIXTURE destination changed")
            return real_replace(source, destination, **kwargs)

        with self.intercept_rename(concurrent_destination):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertEqual(file_bytes(self.destination), {"concurrent.txt": b"retain concurrent install"})
        self.assert_backup_retained(raised.exception, previous)

    def test_unexpected_symlink_at_publication_is_not_removed_or_followed(self):
        previous = self.seed_destination()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("retain outside")
        outside_before = snapshot(outside, strict=True)
        plan = self.plan(replace=True)
        real_replace = os.replace

        def concurrent_link(source, destination, **kwargs):
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if destination_path == self.destination and (source_path / "SKILL.md").is_file():
                self.destination.symlink_to(outside, target_is_directory=True)
                raise OSError("PRIVATE_FIXTURE destination changed")
            return real_replace(source, destination, **kwargs)

        with self.intercept_rename(concurrent_link):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertTrue(self.destination.is_symlink())
        self.assertEqual(os.readlink(self.destination), str(outside))
        self.assertEqual(snapshot(outside, strict=True), outside_before)
        self.assert_backup_retained(raised.exception, previous)

    def test_destination_changed_after_preflight_is_rejected_without_writes(self):
        plan = self.plan()
        self.seed_destination()
        before = snapshot(self.root, strict=True)
        with self.assertRaises(installer.InstallError):
            skill_installer.install(plan)
        self.assertEqual(snapshot(self.root, strict=True), before)

    def test_destination_is_checked_again_after_candidate_preparation(self):
        previous = self.seed_destination()
        plan = self.plan(replace=True)
        saved = self.root / "concurrently-moved-install"
        real_prepare = skill_installer.prepare_candidate

        def concurrent_change(plan, work):
            candidate = real_prepare(plan, work)
            self.destination.rename(saved)
            self.destination.mkdir()
            (self.destination / "concurrent.txt").write_text("retain")
            return candidate

        with mock.patch.object(skill_installer, "prepare_candidate", concurrent_change):
            with self.assertRaises(installer.InstallError):
                skill_installer.install(plan)
        self.assertEqual(file_bytes(self.destination), {"concurrent.txt": b"retain"})
        self.assertEqual(snapshot(saved), previous)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_changed_project_ancestor_is_rejected_without_writes(self):
        project = self.root / "project"
        project.mkdir()
        plan = self.plan(project=project)
        project.rename(self.root / "original-project")
        project.mkdir()
        before = snapshot(self.root, strict=True)
        with self.assertRaises(installer.InstallError):
            skill_installer.install(plan)
        self.assertEqual(snapshot(self.root, strict=True), before)

    def test_parent_replaced_by_a_link_before_staging_is_not_written_through(self):
        plan = self.plan()
        outside = self.root / "outside"
        outside.mkdir()
        moved_parent = self.root / "moved-parent"
        real_mkdir = os.mkdir
        outside_before = {}
        injected = False

        def swap_parent_before_staging(path, mode=0o777, *, dir_fd=None):
            nonlocal injected
            work = self.operation_path(path, dir_fd)
            result = real_mkdir(path, mode, dir_fd=dir_fd)
            if (not injected and work.parent == self.destination.parent
                    and work.name.startswith(".project-init-install-")):
                injected = True
                self.destination.parent.rename(moved_parent)
                foreign_work = outside / work.name
                foreign_work.mkdir()
                (foreign_work / "keep.txt").write_text("retain outside work")
                outside_before.update(snapshot(outside, strict=True))
                self.destination.parent.symlink_to(outside, target_is_directory=True)
            return result

        with mock.patch.object(skill_installer.os, "mkdir", swap_parent_before_staging):
            with self.assertRaises(installer.InstallError):
                skill_installer.install(plan)
        self.assertTrue(injected, "The temporary directory creation was not exercised.")
        self.assertEqual(snapshot(outside, strict=True), outside_before)
        self.assertTrue(self.destination.parent.is_symlink())

    def rollback_destination_swap(self, *, replace):
        previous = self.seed_destination() if replace else None
        plan = self.plan(replace=replace)
        held_candidate = self.root / "held-candidate"
        real_replace = os.replace
        publication_interrupted = False
        moved_unexpected = None

        def swap_after_rollback_check(source, destination, **kwargs):
            nonlocal publication_interrupted, moved_unexpected
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if publication_interrupted and source_path == self.destination:
                real_replace(self.destination, held_candidate)
                self.destination.mkdir()
                (self.destination / "concurrent.txt").write_text("retain concurrent directory")
                moved_unexpected = destination_path
                return real_replace(source, destination, **kwargs)
            candidate = (source_path / "SKILL.md").is_file()
            result = real_replace(source, destination, **kwargs)
            if destination_path == self.destination and candidate:
                publication_interrupted = True
                raise KeyboardInterrupt
            return result

        with self.intercept_rename(swap_after_rollback_check):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertIsNotNone(moved_unexpected, "The rollback rename was not exercised.")
        self.assertTrue(
            (moved_unexpected / "concurrent.txt").is_file(),
            "Rollback deleted the concurrent directory: " + str(raised.exception),
        )
        self.assertEqual(
            (moved_unexpected / "concurrent.txt").read_text(), "retain concurrent directory",
        )
        self.assertIn(str(moved_unexpected.parent), str(raised.exception))
        self.assertNotIn("restored", str(raised.exception).lower())
        self.assertNotIn("removed", str(raised.exception).lower())
        if replace:
            self.assert_backup_retained(raised.exception, previous)

    def test_first_install_rollback_retains_directory_swapped_during_rename(self):
        self.rollback_destination_swap(replace=False)

    def test_replacement_rollback_retains_directory_swapped_during_rename(self):
        self.rollback_destination_swap(replace=True)

    def test_candidate_creation_cannot_follow_parent_link_swapped_after_check(self):
        plan = self.plan()
        outside = self.root / "outside"
        outside.mkdir()
        moved_parent = self.root / "moved-parent"
        real_mkdir = os.mkdir
        real_path_mkdir = Path.mkdir
        outside_before = {}
        injected = False

        def swap_at_candidate_creation(path, dir_fd=None):
            nonlocal injected
            resolved = self.operation_path(path, dir_fd)
            if (not injected and resolved.name == "project-init"
                    and resolved.parent.parent == self.destination.parent):
                injected = True
                self.destination.parent.rename(moved_parent)
                foreign_work = outside / resolved.parent.name
                foreign_work.mkdir()
                (foreign_work / "keep.txt").write_text("retain outside")
                outside_before.update(snapshot(outside, strict=True))
                self.destination.parent.symlink_to(outside, target_is_directory=True)

        def mkdir_at(path, mode=0o777, *, dir_fd=None):
            swap_at_candidate_creation(path, dir_fd)
            return real_mkdir(path, mode, dir_fd=dir_fd)

        def mkdir_path(path, *args, **kwargs):
            swap_at_candidate_creation(path)
            return real_path_mkdir(path, *args, **kwargs)

        with mock.patch.object(skill_installer.os, "mkdir", mkdir_at), \
                mock.patch.object(Path, "mkdir", mkdir_path):
            with self.assertRaises(installer.InstallError):
                skill_installer.install(plan)
        self.assertTrue(injected, "The candidate directory creation was not exercised.")
        self.assertEqual(snapshot(outside, strict=True), outside_before)

    def test_publication_parent_swap_neither_writes_outside_nor_reports_success(self):
        plan = self.plan()
        expected = file_bytes(self.skill)
        outside = self.root / "outside"
        outside.mkdir()
        outside_before = snapshot(outside, strict=True)
        moved_parent = self.root / "moved-parent"
        real_replace = os.replace
        injected = False

        def swap_at_publication(source, destination, **kwargs):
            nonlocal injected
            source_path = self.operation_path(source, kwargs.get("src_dir_fd"))
            destination_path = self.operation_path(destination, kwargs.get("dst_dir_fd"))
            if (destination_path == self.destination
                    and (source_path / "SKILL.md").is_file()):
                injected = True
                self.destination.parent.rename(moved_parent)
                self.destination.parent.symlink_to(outside, target_is_directory=True)
            return real_replace(source, destination, **kwargs)

        with self.intercept_rename(swap_at_publication):
            with self.assertRaises(installer.InstallError) as raised:
                skill_installer.install(plan)
        self.assertTrue(injected, "The publication rename was not exercised.")
        self.assertEqual(snapshot(outside, strict=True), outside_before)
        self.assertEqual(file_bytes(moved_parent / "project-init"), expected)
        self.assertIn("review", str(raised.exception).lower())

    def test_missing_descriptor_capabilities_fail_preflight_without_writes(self):
        cases = (
            ("O_NOFOLLOW", 0), ("O_DIRECTORY", 0),
            ("supports_dir_fd", set()), ("supports_fd", set()),
            ("supports_follow_symlinks", set()),
        )
        for name, value in cases:
            with self.subTest(capability=name):
                before = snapshot(self.root, strict=True)
                with mock.patch.object(skill_installer.os, name, value):
                    with self.assertRaises(installer.InstallError) as raised:
                        self.plan()
                self.assertIn("requires", str(raised.exception).lower())
                self.assertEqual(snapshot(self.root, strict=True), before)

    def git_environment(self):
        return {
            **self.environment, "PATH": os.defpath,
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        }

    def git(self, project, *args):
        executable = shutil.which("git", path=os.defpath)
        if executable is None:
            self.skipTest("Local Git is required for repository preservation checks.")
        completed = subprocess.run(
            [executable, *args], cwd=project, env=self.git_environment(),
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout

    def initialize_git(self, project):
        self.git(project, "init", "-q")
        self.git(project, "add", ".")
        self.git(
            project, "-c", "user.name=Skill install tests",
            "-c", "user.email=skill-tests@example.invalid", "commit", "-qm", "Fixture",
        )

    def test_installed_auditor_runs_read_only_on_a_separate_git_project(self):
        completed = self.run_installer("--mode", "skill")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        project = self.root / "audit-project"
        project.mkdir()
        (project / "package.json").write_text(json.dumps({"name": "standalone-runtime"}))
        (project / "Makefile").write_text("test:\n\t@touch forbidden-script-execution\n")
        self.initialize_git(project)
        before_project = snapshot(project, strict=True)
        before_skill = snapshot(self.destination, strict=True)
        audited = subprocess.run(
            [sys.executable, "-S", str(self.destination / "scripts/project_audit.py"),
             "inspect", str(project)],
            cwd=self.root, env=self.git_environment(), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(json.loads(audited.stdout)["project"]["name"], "standalone-runtime")
        self.assertEqual(snapshot(project, strict=True), before_project)
        self.assertEqual(snapshot(self.destination, strict=True), before_skill)

    def test_dry_run_and_install_leave_source_git_state_unchanged(self):
        self.initialize_git(self.source)
        (self.source / "README.md").write_text("staged source edit\n")
        self.git(self.source, "add", "README.md")
        (self.source / "README.md").write_text("unstaged source edit\n")
        (self.source / "untracked.txt").write_text("retain untracked content\n")
        before = snapshot(self.source, strict=True)
        status = self.git(self.source, "status", "--porcelain=v1", "--untracked-files=all")
        for extra in (("--dry-run",), ()):
            with self.subTest(dry_run=bool(extra)):
                completed = self.run_installer("--mode", "skill", *extra)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(snapshot(self.source, strict=True), before)
                self.assertEqual(
                    self.git(self.source, "status", "--porcelain=v1", "--untracked-files=all"),
                    status,
                )


if __name__ == "__main__":
    unittest.main()
