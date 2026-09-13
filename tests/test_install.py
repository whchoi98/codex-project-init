"""Installer transactions with small CLI doubles and optional Codex trials.

Deterministic tests simulate external CLI contracts while payload, marketplace,
and backup operations use real temporary directories. Optional integration tests
also run installed helpers and the real CLI's read-only capability probe. No test
reads credentials or changes the test process's HOME or CODEX_HOME.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts import install as installer


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/install/helper_contract.py"
NAME = "codex-project-init"
HELPER_NAMES = (
    "create_basic_plugin.py", "read_marketplace_name.py", "update_plugin_cachebuster.py",
)


def snapshot(root):
    result = {}
    if not root.exists():
        return result
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = ("symlink", os.readlink(path))
            elif path.is_file():
                result[relative] = ("file", path.read_bytes(), path.stat().st_mode)
            else:
                result[relative] = ("directory", path.stat().st_mode)
    return result


class InstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-init-install-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.codex_home = self.root / "codex-state"
        self.helpers = self.codex_home / "skills/.system/plugin-creator/scripts"
        self.helpers.mkdir(parents=True)
        for name in HELPER_NAMES:
            shutil.copyfile(FIXTURE, self.helpers / name)
        self.source = self.root / "source"
        shutil.copytree(
            ROOT, self.source,
            ignore=shutil.ignore_patterns(".git", "dist", "__pycache__", "tests"),
        )
        manifest_path = self.source / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "1.2.3+codex.old-token"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.destination = self.home / "plugins" / NAME
        self.marketplace = self.home / ".agents/plugins/marketplace.json"
        self.cli = self.root / "bin/codex"
        self.cli.parent.mkdir()
        self.cli.write_text(
            "#!" + sys.executable + "\n"
            "import json, os, pathlib, sys\n"
            "if sys.argv[1:] == ['plugin', 'add', '--help']:\n"
            "    print('Usage: codex plugin add [OPTIONS] <PLUGIN>')\n"
            "    raise SystemExit(0)\n"
            "if sys.argv[1:] != ['plugin', 'add', "
            "'codex-project-init@' + os.environ.get('TEST_MARKETPLACE', 'personal')]:\n"
            "    raise SystemExit(81)\n"
            "home = pathlib.Path(os.environ['HOME'])\n"
            "destination = home / 'plugins/codex-project-init'\n"
            "manifest = json.loads((destination / '.codex-plugin/plugin.json').read_text())\n"
            "assert manifest['name'] == 'codex-project-init'\n"
            "assert '+codex.' in manifest['version']\n"
            "market = json.loads((home / '.agents/plugins/marketplace.json').read_text())\n"
            "assert any(p['name'] == 'codex-project-init' for p in market['plugins'])\n"
            "cache = pathlib.Path(os.environ['CODEX_HOME']) / 'test-cli-cache'\n"
            "cache.mkdir(exist_ok=True)\n"
            "(cache / 'attempt.json').write_text(json.dumps(sys.argv[1:]))\n"
            "if os.environ.get('TEST_REMOVE_SOURCE'):\n"
            "    import shutil\n"
            "    shutil.rmtree(destination)\n"
            "print('PRIVATE_CLI_STDOUT')\n"
            "print('PRIVATE_CLI_STDERR', file=sys.stderr)\n"
            "raise SystemExit(int(os.environ.get('TEST_CODEX_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.cli.chmod(0o755)
        self.environment = {
            "HOME": str(self.home),
            "CODEX_HOME": str(self.codex_home),
            "PATH": str(self.cli.parent) + os.pathsep + os.defpath,
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def run_installer(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(self.source / "scripts/install.py"), *args],
            env=self.environment, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=30,
        )

    def seed_marketplace(self, *, include_plugin=False, name="personal"):
        entries = [
            {
                "name": "other-plugin",
                "source": {"source": "local", "path": "./plugins/other-plugin"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
                "category": "Custom",
                "extra": {"keep": [1, "unchanged"]},
            },
        ]
        if include_plugin:
            entries.append({
                "name": NAME,
                "source": {"source": "local", "path": "./plugins/" + NAME},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            })
        payload = {
            "name": name, "interface": {"displayName": "My personal tools"},
            "plugins": entries, "custom": {"retain": True},
        }
        self.marketplace.parent.mkdir(parents=True, exist_ok=True)
        self.marketplace.write_text(json.dumps(payload), encoding="utf-8")
        self.environment["TEST_MARKETPLACE"] = name
        return payload

    def seed_destination(self):
        self.destination.mkdir(parents=True)
        (self.destination / "orphan.txt").write_text("previous user content")
        (self.destination / ".codex-plugin").mkdir()
        (self.destination / ".codex-plugin/plugin.json").write_text(
            json.dumps({"name": NAME, "version": "0.0.1"}),
        )
        return snapshot(self.destination)

    def assert_rejected_without_writes(self, *args):
        before = snapshot(self.root)
        completed = self.run_installer(*args)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(snapshot(self.root), before)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)
        self.assertNotIn("Shared distribution support is missing", completed.stderr)
        return completed

    def test_dry_run_performs_preflight_without_creating_home(self):
        before = snapshot(self.root)
        completed = self.run_installer("--dry-run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan["destination"], str(self.destination))
        self.assertTrue(plan["add_marketplace_entry"])
        self.assertFalse(self.home.exists())
        self.assertEqual(snapshot(self.root), before)

    def test_dry_run_rejects_payload_symlink(self):
        secret = self.root / "outside"
        secret.write_text("PRIVATE_OUTSIDE")
        (self.source / "skills/project-init/linked.txt").symlink_to(secret)
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_missing_and_nonexecutable_codex(self):
        for executable in (self.root / "missing", self.root / "nonexecutable"):
            with self.subTest(executable=executable.name):
                if executable.name == "nonexecutable":
                    executable.write_text("not an executable")
                    executable.chmod(0o600)
                self.assert_rejected_without_writes("--dry-run", "--codex", str(executable))

    def unsupported_codex(self, *, returncode=2):
        self.cli.write_text(
            "#!" + sys.executable + "\n"
            "import sys\n"
            "print('Usage: legacy-codex [OPTIONS]')\n"
            "print('PRIVATE_UNSUPPORTED_CLI', file=sys.stderr)\n"
            "raise SystemExit(" + str(returncode) + ")\n",
            encoding="utf-8",
        )

    def test_dry_run_rejects_an_executable_without_plugin_support(self):
        self.unsupported_codex()
        self.assert_rejected_without_writes("--dry-run")

    def test_generic_help_success_does_not_prove_plugin_support(self):
        self.unsupported_codex(returncode=0)
        self.assert_rejected_without_writes("--dry-run")

    def test_unsupported_cli_fails_before_first_install_writes(self):
        self.unsupported_codex()
        completed = self.run_installer()
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(self.home.exists())
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_unsupported_cli_preserves_existing_marketplace_and_source(self):
        self.seed_destination()
        self.seed_marketplace()
        self.unsupported_codex()
        before = snapshot(self.home)
        completed = self.run_installer("--replace")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(snapshot(self.home), before)
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_dry_run_rejects_file_and_dangling_link_destinations(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_text("keep")
        self.assert_rejected_without_writes("--dry-run", "--replace")
        self.destination.unlink()
        self.destination.symlink_to(self.root / "absent")
        self.assert_rejected_without_writes("--dry-run", "--replace")

    def test_dry_run_rejects_symlinked_plugin_parent(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.home.mkdir()
        (self.home / "plugins").symlink_to(elsewhere, target_is_directory=True)
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_symlinked_marketplace_parent(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.home.mkdir()
        (self.home / ".agents").symlink_to(elsewhere, target_is_directory=True)
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_missing_helper_import(self):
        helper = self.helpers / "create_basic_plugin.py"
        helper.write_text("import missing_helper_dependency\n" + helper.read_text())
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_malformed_existing_marketplace(self):
        self.seed_marketplace()
        self.marketplace.write_text(json.dumps({
            "name": "personal", "interface": "invalid", "plugins": [],
        }))
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_invalid_marketplace_entries(self):
        malformed = [
            [],
            {"name": "personal", "plugins": {}},
            {"name": "personal", "plugins": ["not-an-entry"]},
            {"name": "personal", "plugins": [{"name": None}]},
            {"name": "PRIVATE_INVALID_NAME;bad", "plugins": []},
            {"name": "personal", "plugins": [
                {"name": NAME, "source": {"source": "local", "path": "./elsewhere"}},
            ]},
            {"name": "personal", "plugins": [
                {"name": "other-plugin"}, {"name": "other-plugin"},
            ]},
        ]
        self.marketplace.parent.mkdir(parents=True)
        for payload in malformed:
            with self.subTest(payload_type=type(payload).__name__):
                self.marketplace.write_text(json.dumps(payload))
                self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_symlink_and_hardlink_marketplace_files(self):
        outside = self.root / "outside.json"
        outside.write_text(json.dumps({"name": "personal", "plugins": []}))
        self.marketplace.parent.mkdir(parents=True)
        self.marketplace.symlink_to(outside)
        self.assert_rejected_without_writes("--dry-run")
        self.marketplace.unlink()
        os.link(outside, self.marketplace)
        self.assert_rejected_without_writes("--dry-run")

    def test_dry_run_rejects_lossy_or_nonstandard_marketplace_json(self):
        self.marketplace.parent.mkdir(parents=True)
        for contents in (
            '{"name":"personal","plugins":[{"name":"keep"}],"plugins":[]}',
            '{"name":"personal","plugins":[],"extra":NaN}',
            '{"name":"personal","plugins":[],"extra":Infinity}',
        ):
            with self.subTest(contents=contents):
                self.marketplace.write_text(contents)
                self.assert_rejected_without_writes("--dry-run")

    def test_destination_requires_explicit_replacement(self):
        self.seed_destination()
        self.assert_rejected_without_writes("--dry-run")

    def test_install_preserves_other_entries_and_marketplace_metadata(self):
        before = self.seed_marketplace(name="my-local-tools")
        completed = self.run_installer()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.startswith("{"), completed.stdout)
        report = json.loads(completed.stdout)
        after = json.loads(self.marketplace.read_text())
        self.assertEqual(after["plugins"][0], before["plugins"][0])
        self.assertEqual(after["interface"], before["interface"])
        self.assertEqual(after["custom"], before["custom"])
        self.assertEqual(len(after["plugins"]), 2)
        self.assertTrue(report["installed_version"].startswith("1.2.3+codex."))
        self.assertEqual(report["installed_version"].count("+codex."), 1)
        self.assertNotIn("old-token", report["installed_version"])
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_install_excludes_unrelated_source_files_and_keeps_source_unchanged(self):
        (self.source / "stale-orphan.txt").write_text("not a plugin file")
        (self.source / ".env").write_text("FIXTURE_TOKEN=PRIVATE_FIXTURE")
        before = snapshot(self.source)
        completed = self.run_installer()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(snapshot(self.source), before)
        self.assertFalse((self.destination / "stale-orphan.txt").exists())
        self.assertFalse((self.destination / ".env").exists())
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_installed_skill_includes_the_complete_auditor_runtime(self):
        completed = self.run_installer()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            snapshot(self.destination / "skills/project-init"),
            snapshot(self.source / "skills/project-init"),
        )
        project = self.root / "sample-project"
        project.mkdir()
        (project / "package.json").write_text(json.dumps({"name": "copied-runtime"}))
        before = snapshot(project)
        audited = subprocess.run(
            [sys.executable, "-B",
             str(self.destination / "skills/project-init/scripts/project_audit.py"),
             "inspect", str(project)],
            env=self.environment, cwd=self.root, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(json.loads(audited.stdout)["project"]["name"], "copied-runtime")
        self.assertEqual(snapshot(project), before)

    def test_replacement_uses_fresh_payload_and_preserves_backup(self):
        previous = self.seed_destination()
        self.seed_marketplace(include_plugin=True)
        marketplace_before = self.marketplace.read_bytes()
        completed = self.run_installer("--replace")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.startswith("{"), completed.stdout)
        report = json.loads(completed.stdout)
        self.assertEqual(snapshot(Path(report["backup"])), previous)
        self.assertFalse((self.destination / "orphan.txt").exists())
        self.assertEqual(self.marketplace.read_bytes(), marketplace_before)
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_cli_failure_restores_existing_source_and_reports_cache_limit(self):
        previous = self.seed_destination()
        self.seed_marketplace(include_plugin=True)
        marketplace_before = self.marketplace.read_bytes()
        self.environment["TEST_CODEX_EXIT"] = "9"
        completed = self.run_installer("--replace")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertEqual(self.marketplace.read_bytes(), marketplace_before)
        self.assertTrue((self.codex_home / "test-cli-cache/attempt.json").is_file())
        self.assertIn("restored", completed.stderr.lower())
        self.assertIn("cache", completed.stderr.lower())
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_first_install_cli_failure_keeps_complete_recoverable_source(self):
        before = self.seed_marketplace()
        self.environment["TEST_CODEX_EXIT"] = "9"
        completed = self.run_installer()
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((self.destination / "skills/project-init/SKILL.md").is_file())
        installed = json.loads((self.destination / ".codex-plugin/plugin.json").read_text())
        self.assertTrue(installed["version"].startswith("1.2.3+codex."))
        marketplace = json.loads(self.marketplace.read_text())
        self.assertEqual(marketplace["plugins"][0], before["plugins"][0])
        self.assertEqual(marketplace["plugins"][1]["name"], NAME)
        self.assertIn("retained", completed.stderr.lower())
        self.assertIn("marketplace", completed.stderr.lower())
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_first_install_cli_failure_without_marketplace_remains_retryable(self):
        self.environment["TEST_CODEX_EXIT"] = "9"
        completed = self.run_installer()
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(self.destination.is_dir())
        payload = json.loads(self.marketplace.read_text())
        self.assertEqual([entry["name"] for entry in payload["plugins"]], [NAME])
        self.environment["TEST_CODEX_EXIT"] = "0"
        retried = self.run_installer("--replace")
        self.assertEqual(retried.returncode, 0, retried.stderr)
        self.assertEqual(json.loads(self.marketplace.read_text()), payload)

    def test_first_install_recovers_source_if_cli_failure_removed_published_copy(self):
        self.environment["TEST_CODEX_EXIT"] = "9"
        self.environment["TEST_REMOVE_SOURCE"] = "1"
        completed = self.run_installer()
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((self.destination / "skills/project-init/SKILL.md").is_file())
        self.assertEqual(
            snapshot(self.destination / "skills/project-init"),
            snapshot(self.source / "skills/project-init"),
        )
        self.assertEqual(json.loads(self.marketplace.read_text())["plugins"][0]["name"], NAME)
        self.assertIn("retained", completed.stderr.lower())
        self.assertNotIn("PRIVATE_", completed.stdout + completed.stderr)

    def test_first_install_helper_failure_leaves_no_destination_or_marketplace(self):
        # The real updater cannot use a non-string version. Shared source
        # validation may reject this even earlier, which is equally safe.
        manifest_path = self.source / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = 123
        manifest_path.write_text(json.dumps(manifest))
        completed = self.run_installer()
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.marketplace.exists())
        self.assertNotIn("Traceback", completed.stderr)

    def test_source_cannot_replace_itself(self):
        self.destination.parent.mkdir(parents=True)
        shutil.move(str(self.source), self.destination)
        self.source = self.destination
        self.assert_rejected_without_writes("--dry-run", "--replace")

    def plan(self, **kwargs):
        return installer.build_plan(
            source=self.source, home=self.home, codex_home=self.codex_home,
            environment=self.environment, **kwargs,
        )

    def test_in_memory_preflight_does_not_change_process_environment(self):
        before = dict(os.environ)
        plan = self.plan()
        self.assertEqual(plan.destination, self.destination)
        self.assertEqual(dict(os.environ), before)
        self.assertFalse(self.home.exists())

    def test_changed_destination_is_rejected_before_installing(self):
        plan = self.plan()
        self.seed_destination()
        before = snapshot(self.root)
        with self.assertRaises(installer.InstallError):
            installer.install(plan)
        self.assertEqual(snapshot(self.root), before)

    def test_changed_marketplace_is_rejected_before_installing(self):
        self.seed_marketplace()
        plan = self.plan()
        self.seed_marketplace(name="changed")
        before = snapshot(self.root)
        with self.assertRaises(installer.InstallError):
            installer.install(plan)
        self.assertEqual(snapshot(self.root), before)

    def test_candidate_helper_failure_preserves_original_source_and_marketplace(self):
        previous = self.seed_destination()
        self.seed_marketplace(include_plugin=True)
        plan = self.plan(replace=True)
        before_marketplace = self.marketplace.read_bytes()
        # Remove the command only after it passed read-only preflight.
        (self.helpers / "update_plugin_cachebuster.py").unlink()
        with self.assertRaises(installer.InstallError):
            installer.install(plan)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertEqual(self.marketplace.read_bytes(), before_marketplace)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])
        self.assertFalse((self.codex_home / "test-cli-cache").exists())

    def test_missing_scaffold_after_preflight_cannot_publish_a_new_marketplace(self):
        plan = self.plan()
        (self.helpers / "create_basic_plugin.py").unlink()
        with self.assertRaises(installer.InstallError):
            installer.install(plan)
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.marketplace.exists())
        self.assertFalse((self.codex_home / "test-cli-cache").exists())

    def test_missing_payload_during_copy_does_not_touch_existing_source(self):
        self.seed_destination()
        self.seed_marketplace(include_plugin=True)
        plan = self.plan(replace=True)
        (self.source / "scripts/install.py").unlink()
        before = snapshot(self.root)
        with self.assertRaises(installer.InstallError):
            installer.install(plan)
        self.assertEqual(snapshot(self.root), before)

    def helper_plan(self, *, existing=False):
        """A direct marketplace/recovery plan does not need payload validation."""
        contents = self.marketplace.read_bytes() if self.marketplace.exists() else None
        return installer.InstallPlan(
            self.source, self.destination, self.marketplace, self.helpers, str(self.cli),
            self.environment.get("TEST_MARKETPLACE", "personal"), not existing, False,
            (), dict(self.environment), contents, None,
        )

    def test_helper_stages_marketplace_without_touching_live_paths(self):
        before = self.seed_marketplace(name="my-tools")
        live_bytes = self.marketplace.read_bytes()
        plan = self.helper_plan()
        work = self.root / "staging"
        work.mkdir()
        staged = installer.prepare_marketplace(plan, work)
        self.assertEqual(self.marketplace.read_bytes(), live_bytes)
        self.assertFalse(self.destination.exists())
        after = json.loads(staged.read_text())
        self.assertEqual(after["name"], before["name"])
        self.assertEqual(after["interface"], before["interface"])
        self.assertEqual(after["plugins"][0], before["plugins"][0])
        self.assertEqual(after["plugins"][1], {
            "name": NAME,
            "source": {"source": "local", "path": "./plugins/" + NAME},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        })
        installer.publish_marketplace(plan, staged)
        self.assertEqual(json.loads(self.marketplace.read_text()), after)
        self.assertNotIn("__pycache__", {p.name for p in self.helpers.rglob("*")})

    def test_marketplace_publish_preserves_a_concurrent_edit(self):
        self.seed_marketplace()
        plan = self.helper_plan()
        work = self.root / "staging"
        work.mkdir()
        staged = installer.prepare_marketplace(plan, work)
        self.seed_marketplace(name="changed")
        before = snapshot(self.home)
        with self.assertRaises(installer.InstallError):
            installer.publish_marketplace(plan, staged)
        self.assertEqual(snapshot(self.home), before)

    def test_rollback_restores_source_over_a_dangling_destination_symlink(self):
        previous = self.seed_destination()
        work = self.root / "staging"
        work.mkdir()
        backup = self.root / "backup" / NAME
        backup.parent.mkdir()
        self.destination.rename(backup)
        self.destination.symlink_to(self.root / "missing-outside", target_is_directory=True)
        state = installer.InstallState(backup=backup, source_published=True)
        message = installer.rollback(self.helper_plan(), state, work)
        self.assertFalse(self.destination.is_symlink())
        self.assertEqual(snapshot(self.destination), previous)
        self.assertIn("restored", message.lower())

    def test_rollback_reports_restoration_when_backup_container_is_not_empty(self):
        previous = self.seed_destination()
        work = self.root / "staging"
        work.mkdir()
        backup = self.root / "backup" / NAME
        backup.parent.mkdir()
        self.destination.rename(backup)
        marker = backup.parent / "keep.txt"
        marker.write_text("unrelated content")
        state = installer.InstallState(backup=backup)
        message = installer.rollback(self.helper_plan(), state, work)
        self.assertEqual(snapshot(self.destination), previous)
        self.assertIn("restored", message.lower())
        self.assertEqual(marker.read_text(), "unrelated content")

    def test_rollback_does_not_follow_a_changed_destination_ancestor(self):
        self.seed_destination()
        work = self.root / "staging"
        work.mkdir()
        backup = self.root / "backup" / NAME
        backup.parent.mkdir()
        self.destination.rename(backup)
        self.destination.parent.rmdir()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / NAME).mkdir()
        (outside / NAME / "keep.txt").write_text("outside content")
        self.destination.parent.symlink_to(outside, target_is_directory=True)
        before = snapshot(outside)
        original = snapshot(backup)
        state = installer.InstallState(backup=backup, source_published=True)
        message = installer.rollback(self.helper_plan(), state, work)
        self.assertEqual(snapshot(outside), before)
        self.assertEqual(snapshot(backup), original)
        self.assertNotIn("restored", message.lower())
        self.assertIn("review", message.lower())


@unittest.skipUnless(
    os.environ.get("PROJECT_INIT_REAL_INTEGRATION") == "1",
    "Set PROJECT_INIT_REAL_INTEGRATION=1 for optional installed Codex trials.",
)
class InstalledCodexContractTests(unittest.TestCase):
    """Use installed tools only in scratch profiles; never run real plugin add.

    PROJECT_INIT_REAL_HELPERS may select a plugin-creator scripts directory.
    PROJECT_INIT_REAL_CODEX may select the CLI for the read-only dry-run trial.
    """

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="installed-codex-contract-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.codex_home = self.root / "state"
        self.environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(self.home), "CODEX_HOME": str(self.codex_home),
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "XDG_CACHE_HOME": str(self.root / "cache"),
            "XDG_DATA_HOME": str(self.root / "data"),
            "TMPDIR": str(self.root), "PYTHONDONTWRITEBYTECODE": "1",
        }
        real_state = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        self.helpers = Path(os.environ.get(
            "PROJECT_INIT_REAL_HELPERS", real_state / "skills/.system/plugin-creator/scripts",
        ))
        if not all((self.helpers / name).is_file() for name in HELPER_NAMES):
            self.skipTest("Installed plugin-creator helpers are unavailable.")

    def strict_snapshot(self, root):
        # Detect rewrites and transient create/delete operations as well as
        # changed bytes. Reading may affect access times, which are excluded.
        times = {}
        for path in [root] + list(root.rglob("*")):
            info = path.lstat()
            times[path.relative_to(root).as_posix()] = (info.st_mtime_ns, info.st_ctime_ns)
        return snapshot(root), times

    def test_real_cli_and_helpers_dry_run_does_not_write_profiles(self):
        executable = shutil.which(os.environ.get("PROJECT_INIT_REAL_CODEX", "codex"))
        if executable is None:
            self.skipTest("A Codex CLI is unavailable.")
        for existing_profile in (False, True):
            with self.subTest(existing_profile=existing_profile):
                if existing_profile:
                    self.codex_home.mkdir()
                    marketplace = self.home / ".agents/plugins/marketplace.json"
                    marketplace.parent.mkdir(parents=True)
                    marketplace.write_text(json.dumps({"name": "personal", "plugins": []}))
                before = self.strict_snapshot(self.root)
                helpers_before = self.strict_snapshot(self.helpers)
                process_environment = dict(os.environ)
                output, errors = io.StringIO(), io.StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    result = installer.main(
                        ["--dry-run", "--codex", executable], source=ROOT,
                        home=self.home, codex_home=self.codex_home,
                        helpers=self.helpers, environment=self.environment,
                    )
                self.assertEqual(result, 0, errors.getvalue())
                report = json.loads(output.getvalue())
                self.assertEqual(report["destination"], str(self.home / "plugins" / NAME))
                self.assertEqual(self.strict_snapshot(self.root), before)
                self.assertEqual(self.strict_snapshot(self.helpers), helpers_before)
                self.assertEqual(dict(os.environ), process_environment)

    def test_real_helpers_prepare_payload_and_preserve_marketplace_entries(self):
        # This executable supports only the capability check. Calling a real
        # install command in this trial would fail, rather than install anything.
        executable = self.root / "probe-only-codex"
        executable.write_text(
            "#!" + sys.executable + "\nimport sys\n"
            "assert sys.argv[1:] == ['plugin', 'add', '--help']\n"
            "print('Usage: codex plugin add [OPTIONS] <PLUGIN>')\n",
        )
        executable.chmod(0o755)
        marketplace = self.home / ".agents/plugins/marketplace.json"
        original = {
            "name": "contract-local", "interface": {"displayName": "Keep this label"},
            "plugins": [{
                "name": "other-plugin",
                "source": {"source": "local", "path": "./plugins/other-plugin"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
                "category": "Custom", "metadata": {"keep": True},
            }],
        }
        marketplace.parent.mkdir(parents=True)
        marketplace.write_text(json.dumps(original))
        before = self.strict_snapshot(self.home)
        helpers_before = self.strict_snapshot(self.helpers)
        manifest_before = (ROOT / ".codex-plugin/plugin.json").read_bytes()
        plan = installer.build_plan(
            source=ROOT, home=self.home, codex_home=self.codex_home,
            helpers=self.helpers, codex=executable, environment=self.environment,
        )
        skill = ROOT / "skills/project-init"
        expected_skill = {
            path.relative_to(skill).as_posix(): path.read_bytes()
            for path in plan.files if skill in path.parents
        }
        work = self.root / "staging"
        work.mkdir()
        candidate, version = installer.prepare_candidate(plan, work)
        staged = installer.prepare_marketplace(plan, work)
        self.assertEqual(self.strict_snapshot(self.home), before)
        source_version = json.loads(manifest_before)["version"].split("+", 1)[0]
        self.assertRegex(version, "^" + re.escape(source_version) + r"\+codex\.[0-9]+$")
        copied_skill = candidate / "skills/project-init"
        self.assertEqual({
            path.relative_to(copied_skill).as_posix(): path.read_bytes()
            for path in copied_skill.rglob("*") if path.is_file()
        }, expected_skill)
        generated = json.loads(staged.read_text())
        self.assertEqual(generated["name"], original["name"])
        self.assertEqual(generated["interface"], original["interface"])
        self.assertEqual(generated["plugins"][0], original["plugins"][0])
        self.assertEqual(generated["plugins"][1], {
            "name": NAME,
            "source": {"source": "local", "path": "./plugins/" + NAME},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        })
        plan.destination.parent.mkdir(parents=True)
        candidate.rename(plan.destination)
        installer.publish_marketplace(plan, staged)
        self.assertEqual(json.loads(marketplace.read_text()), generated)
        self.assertEqual(self.strict_snapshot(self.helpers), helpers_before)
        self.assertEqual((ROOT / ".codex-plugin/plugin.json").read_bytes(), manifest_before)


if __name__ == "__main__":
    unittest.main()
