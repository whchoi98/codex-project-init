import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/project-init/scripts/project_audit.py"


class ProjectAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="project-init-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def core(self):
        self.write("AGENTS.md", "# Project\n\nUse the declared validation commands.\n")
        self.write("README.md", "# Example\n\n[Architecture](docs/architecture.md)\n")
        self.write("CHANGELOG.md", "# Changes\n\n## [Unreleased]\n")
        self.write(".gitignore", ".env\n.env.*\n!.env.example\n")
        self.write("docs/README.md", "# Docs\n\n[Architecture](architecture.md)\n")
        self.write("docs/architecture.md", "# Architecture\n\n[Project](../README.md)\n")
        self.write("docs/onboarding.md", "# Setup\n\nUse the project README.\n")

    def git(self, *args):
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        return subprocess.check_output(
            ["git", "-c", "core.hooksPath=" + os.devnull, "-C", str(self.root), *args],
            stderr=subprocess.PIPE, env=environment,
        ).decode().strip()

    def audit(self, mode="inspect", *args, target=None, env=None, timeout=15):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), mode, str(target or self.root), *args],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def snapshot(self):
        return {
            str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()
        }

    def test_inspection_detects_commands_without_executing_or_modifying_project(self):
        self.core()
        self.write("package.json", json.dumps({
            "name": "example", "version": "1.2.3", "packageManager": "pnpm@9.0.0",
            "scripts": {"test": "touch should-never-exist", "lint": "PRIVATE_SCRIPT_VALUE"},
            "dependencies": {"@xterm/headless": "6.0.0"},
        }))
        self.write(".env", "TOKEN=PRIVATE_ENV_VALUE\n")
        before = self.snapshot()
        code, report = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(report["project"]["name"], "example")
        self.assertEqual(report["project"]["commands"]["test"], "pnpm run test")
        self.assertIn("terminal", report["project"]["layers"])
        self.assertFalse(report["git"]["valid"])
        self.assertNotIn("PRIVATE_", json.dumps(report))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root / "should-never-exist").exists())
        self.assertFalse((self.root / ".git").exists())

    def test_document_check_passes_without_claiming_git_readiness(self):
        self.core()
        code, report = self.audit("check")
        self.assertEqual(code, 0)
        self.assertFalse(report["git"]["valid"])
        self.assertFalse(any(f["severity"] == "error" for f in report["findings"]))
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertIn("git_missing", {f["code"] for f in report["findings"]})
        self.assertFalse(report["scan"]["complete"])

    def test_empty_git_directory_is_not_a_repository(self):
        self.core()
        (self.root / ".git").mkdir()
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertFalse(report["git"]["valid"])

    def test_missing_core_documents_are_actionable_findings(self):
        code, report = self.audit("check")
        self.assertEqual(code, 1)
        missing = {f["path"] for f in report["findings"] if f["code"] == "missing_document"}
        self.assertIn("README.md", missing)
        self.assertIn("AGENTS.md", missing)
        self.assertIn("docs/architecture.md", missing)

    def test_links_resolve_relative_paths_and_ignore_code_examples(self):
        self.core()
        self.write("docs/space name.md", "# Space\n")
        self.write("docs/a(b).md", "# Parentheses\n")
        self.write("docs/architecture.md",
                   "# Architecture\n[ok](space%20name.md)\n[also](a(b).md)\n"
                   "```markdown\n[example](not-real.md)\n```\n"
                   "[web](https://example.invalid/no-request)\n")
        code, report = self.audit("check")
        self.assertEqual(code, 0, report["findings"])
        self.write("docs/broken.md", "# Broken\n[bad](missing.md)\n")
        code, report = self.audit("check")
        self.assertEqual(code, 1)
        self.assertTrue(any(f["code"] == "broken_link" and f["path"] == "docs/broken.md"
                            for f in report["findings"]))

    def test_external_symlink_is_not_read(self):
        self.core()
        outside = tempfile.TemporaryDirectory(prefix="project-init-outside-")
        self.addCleanup(outside.cleanup)
        secret = Path(outside.name) / "private.md"
        secret.write_text("PRIVATE_EXTERNAL_VALUE")
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(secret)
        code, report = self.audit("check")
        self.assertEqual(code, 1)
        self.assertNotIn("PRIVATE_EXTERNAL_VALUE", json.dumps(report))
        self.assertIn("external_symlink", {f["code"] for f in report["findings"]})

    def test_dependency_directories_are_not_audited(self):
        self.core()
        self.write("node_modules/vendor/README.md", "[broken](missing.md)\n")
        code, report = self.audit("check")
        self.assertEqual(code, 0)
        self.assertNotIn("node_modules/vendor/README.md", report["documents"])

    def test_staged_scan_reads_index_instead_of_clean_working_tree(self):
        self.core()
        self.git("init", "-b", "main")
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        self.write("notes.txt", marker + "\nfixture\n")
        self.git("add", "notes.txt")
        self.write("notes.txt", "working tree is now clean\n")
        index = (self.root / ".git/index").read_bytes()
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertTrue(any(f["code"] == "staged_secret" for f in report["findings"]))
        self.assertNotIn(marker, json.dumps(report))
        self.assertEqual((self.root / ".git/index").read_bytes(), index)
        self.git("add", "notes.txt")
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 0, report["findings"])

    def test_staged_env_example_is_allowed_but_real_env_path_is_reported(self):
        self.core()
        self.git("init", "-b", "main")
        self.write(".env.example", "API_KEY=example\n")
        self.git("add", ".env.example")
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 0, report["findings"])
        self.write(".env", "API_KEY=example\n")
        self.git("add", "-f", ".env")
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertIn("staged_credential_file", {f["code"] for f in report["findings"]})

    def test_remote_credentials_are_redacted_without_changing_remote(self):
        self.core()
        self.git("init", "-b", "main")
        remote = "https://name:PRIVATE_PASSWORD@example.invalid/org/repo.git?token=PRIVATE_QUERY"
        self.git("remote", "add", "origin", remote)
        code, report = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(report["git"]["remote"], "https://example.invalid/org/repo.git")
        self.assertNotIn("PRIVATE_", json.dumps(report))
        self.assertEqual(self.git("remote", "get-url", "origin"), remote)

    def test_existing_document_profile_does_not_require_full_initialization(self):
        self.write("README.md", "# Small tool\n\nRun the tool locally.\n")
        code, report = self.audit("check", "--profile", "existing")
        self.assertEqual(code, 0, report["findings"])
        self.assertNotIn("missing_document", {f["code"] for f in report["findings"]})
        code, report = self.audit(
            "check", "--profile", "existing", "--require-document", "guide/start.md"
        )
        self.assertEqual(code, 1)
        self.assertTrue(any(f["code"] == "missing_document"
                            and f["path"] == "guide/start.md" for f in report["findings"]))

    def test_core_profile_recognizes_existing_equivalent_layout(self):
        self.core()
        (self.root / "docs/architecture.md").rename(self.root / "ARCHITECTURE.md")
        (self.root / "docs/README.md").rename(self.root / "docs/index.md")
        (self.root / "docs/onboarding.md").rename(self.root / "docs/getting-started.md")
        self.write("README.md", "# Project\n\n[Architecture](ARCHITECTURE.md)\n")
        self.write("docs/index.md", "# Docs\n\n[Architecture](../ARCHITECTURE.md)\n")
        self.write("ARCHITECTURE.md", "# Architecture\n\n[Project](README.md)\n")
        code, report = self.audit("check")
        self.assertEqual(code, 0, report["findings"])

    def test_inline_code_comments_and_escaped_links_are_not_document_links(self):
        self.core()
        self.write("README.md", '# Project\n\n`[example](not-a-file.md)`\n'
                   '<!-- [draft](missing.md) -->\n'
                   '\\[literal](not-a-link.md)\n'
                   '[real](docs/architecture.md)\n')
        code, report = self.audit("check")
        self.assertEqual(code, 0, report["findings"])

    def test_link_paths_decode_markdown_escapes_and_html_entities(self):
        self.core()
        self.write("docs/a(b).md", "# Parentheses\n")
        self.write("docs/a&b.md", "# Ampersand\n")
        self.write("README.md", '# Project\n\n[Escaped](docs/a\\(b\\).md)\n'
                   '<a href="docs/a&amp;b.md">HTML link</a>\n')
        code, report = self.audit("check")
        self.assertEqual(code, 0, report["findings"])

    def test_external_directory_symlink_is_reported_without_reading_it(self):
        self.core()
        outside = tempfile.TemporaryDirectory(prefix="project-init-outside-")
        self.addCleanup(outside.cleanup)
        target = Path(outside.name)
        (target / "README.md").write_text("PRIVATE_DIRECTORY_VALUE\n")
        shutil.rmtree(self.root / "docs")
        (self.root / "docs").symlink_to(target, target_is_directory=True)
        before = self.snapshot()
        code, report = self.audit("check")
        self.assertEqual(code, 1)
        self.assertIn("docs", report["excluded_external_links"])
        self.assertNotIn("PRIVATE_DIRECTORY_VALUE", json.dumps(report))
        self.assertEqual(self.snapshot(), before)

    def test_symlink_loop_is_a_finding_instead_of_a_traceback(self):
        self.core()
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to("README.md")
        code, report = self.audit("check")
        self.assertEqual(code, 1)
        self.assertTrue(any(f["path"] == "README.md" for f in report["findings"]))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires a filesystem with FIFOs")
    def test_special_document_file_never_blocks_the_auditor(self):
        self.core()
        os.mkfifo(self.root / "pipe.md")
        try:
            code, report = self.audit("check", timeout=3)
        except subprocess.TimeoutExpired:
            self.fail("The read-only auditor blocked while reading a FIFO.")
        self.assertEqual(code, 0, report["findings"])
        self.assertFalse(report["scan"]["complete"])
        self.assertTrue(any(f["path"] == "pipe.md" for f in report["findings"]))

    def test_git_ignored_generated_docs_do_not_create_false_link_failures(self):
        self.core()
        self.git("init", "-b", "main")
        self.write(".gitignore", "generated/\n")
        self.write("generated/output.md", "[irrelevant](missing.md)\n")
        code, report = self.audit("check")
        self.assertEqual(code, 0, report["findings"])
        self.assertNotIn("generated/output.md", report["documents"])

    def test_git_environment_cannot_redirect_audit_to_another_repository(self):
        self.core()
        self.git("init", "-b", "main")
        outside = tempfile.TemporaryDirectory(prefix="project-init-git-outside-")
        self.addCleanup(outside.cleanup)
        other = Path(outside.name)
        subprocess.run(["git", "init", "-b", "outside", str(other)],
                       capture_output=True, check=True)
        env = {**os.environ, "GIT_DIR": str(other / ".git"),
               "GIT_WORK_TREE": str(other)}
        code, report = self.audit(env=env)
        self.assertEqual(code, 0)
        self.assertTrue(report["git"]["valid"])
        self.assertEqual(report["git"]["root"], str(self.root))

    def test_repository_clean_filter_is_never_executed(self):
        self.assert_filter_not_executed("unsafe")

    def test_filter_name_with_equals_cannot_bypass_execution_prevention(self):
        self.assert_filter_not_executed("review=driver")

    def assert_filter_not_executed(self, driver):
        self.core()
        self.git("init", "-b", "main")
        self.write(".gitattributes", "*.txt filter=" + driver + "\n")
        self.write("tracked.txt", "original\n")
        self.git("add", "tracked.txt", ".gitattributes")
        marker = self.root / "filter-executed"
        executable = self.write("filter.py", "from pathlib import Path\n"
                                f"Path({str(marker)!r}).write_text('executed')\n"
                                "import sys\nsys.stdout.write(sys.stdin.read())\n")
        self.git("config", "filter." + driver + ".clean", f'"{sys.executable}" "{executable}"')
        self.git("config", "filter." + driver + ".required", "true")
        self.write("tracked.txt", "modified content\n")
        before = self.snapshot()
        code, report = self.audit()
        self.assertFalse(marker.exists(), "Git executed a clean filter during inspection.")
        self.assertEqual(code, 0, report["findings"])
        self.assertEqual(self.snapshot(), before)
        code, report = self.audit("check", "--for-commit")
        self.assertFalse(marker.exists(), "Git executed a project-defined clean filter.")
        self.assertEqual(code, 0, report["findings"])
        self.assertEqual(self.snapshot(), before)

    def test_commit_preflight_respects_subproject_scope(self):
        parent = self.root
        package = parent / "packages/api"
        package.mkdir(parents=True)
        self.root = package
        self.core()
        self.write("module.py", "value = 1\n")
        self.root = parent
        self.git("init", "-b", "main")
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        self.write("sibling-secret.txt", marker + "\nfixture\n")
        self.git("add", "packages/api/module.py", "sibling-secret.txt")
        before = self.snapshot()
        code, report = self.audit("check", "--for-commit", target=package)
        self.assertEqual(code, 0, report["findings"])
        self.assertEqual(report["git"]["root"], str(parent))
        self.assertEqual(report["git"]["staged_paths"], ["module.py"])
        self.assertNotIn("sibling-secret.txt", json.dumps(report))
        self.assertEqual(self.snapshot(), before)

    def test_malformed_manifest_is_reported_without_echoing_its_contents(self):
        self.core()
        self.write("package.json", '{"name": "PRIVATE_BROKEN_VALUE",')
        code, report = self.audit()
        self.assertEqual(code, 0)
        self.assertTrue(any(f["path"] == "package.json" for f in report["findings"]))
        self.assertNotIn("PRIVATE_BROKEN_VALUE", json.dumps(report))

    def test_oversized_document_marks_coverage_incomplete(self):
        self.core()
        self.write("docs/large.md", "x" * (1024 * 1024 + 1))
        code, report = self.audit("check")
        self.assertEqual(code, 0)
        self.assertFalse(report["scan"]["complete"])
        self.assertTrue(any(f["path"] == "docs/large.md" for f in report["findings"]))

    def test_python_project_metadata_has_evidence_without_executing_setup(self):
        self.write("pyproject.toml", '[project]\nname = "example-python"\n'
                   'version = "2.3.4" # release authority\n'
                   "description = 'A local Python tool'\n")
        self.write("setup.py", "raise RuntimeError('must not execute')\n")
        self.write("Makefile", "test:\n\tpython3 -m unittest\n")
        code, report = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(report["project"]["name"], "example-python")
        self.assertEqual(report["project"]["version"], "2.3.4")
        self.assertEqual(report["project"]["commands"]["test"], "make test")
        self.assertEqual(report["project"]["command_evidence"]["test"]["path"], "Makefile")

    @unittest.skipUnless(os.open in os.supports_dir_fd, "requires directory-relative open")
    def test_parent_directory_swap_cannot_redirect_a_file_read_outside_target(self):
        self.core()
        outside = tempfile.TemporaryDirectory(prefix="project-init-swap-outside-")
        self.addCleanup(outside.cleanup)
        target = Path(outside.name)
        (target / "architecture.md").write_text("PRIVATE_SWAPPED_VALUE\n")
        spec = importlib.util.spec_from_file_location(
            "audit_filesystem", SCRIPT.parent / "project_init_audit/filesystem.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_open = os.open
        switched = False

        def swap_then_open(*args, **kwargs):
            nonlocal switched
            if not switched:
                switched = True
                (self.root / "docs").rename(self.root / "original-docs")
                (self.root / "docs").symlink_to(target, target_is_directory=True)
            return original_open(*args, **kwargs)

        with mock.patch.object(module.os, "open", side_effect=swap_then_open):
            with self.assertRaises(module.FileNotRead):
                module.safe_read(self.root, "docs/architecture.md")

    def test_symlinked_git_metadata_is_not_followed_outside_target(self):
        self.core()
        outside = tempfile.TemporaryDirectory(prefix="project-init-metadata-outside-")
        self.addCleanup(outside.cleanup)
        other = Path(outside.name)
        subprocess.run(["git", "init", "-b", "outside", str(other)],
                       capture_output=True, check=True)
        (self.root / ".git").symlink_to(other / ".git", target_is_directory=True)
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertFalse(report["git"]["valid"])
        self.assertFalse(report["scan"]["complete"])

    def test_external_git_config_symlink_is_rejected_before_git_reads_it(self):
        self.core()
        self.git("init", "-b", "main")
        outside = tempfile.TemporaryDirectory(prefix="project-init-config-outside-")
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "config"
        target.write_bytes((self.root / ".git/config").read_bytes()
                           + b'[remote "origin"]\nurl = https://example.invalid/OUTSIDE_METADATA_VALUE\n')
        (self.root / ".git/config").unlink()
        (self.root / ".git/config").symlink_to(target)
        for mode, args in (("inspect", ()), ("check", ("--for-commit",))):
            with self.subTest(mode=mode):
                code, report = self.audit(mode, *args)
                self.assertEqual(code, 0 if mode == "inspect" else 1)
                self.assertFalse(report["git"]["valid"])
                self.assertFalse(report["scan"]["complete"])
                self.assertNotIn("OUTSIDE_METADATA_VALUE", json.dumps(report))

    def test_subproject_scope_preserves_leading_space_in_path(self):
        parent = self.root
        package = parent / " spaced package"
        package.mkdir()
        self.root = package
        self.core()
        self.write("module.py", "value = 1\n")
        self.root = parent
        self.git("init", "-b", "main")
        self.git("add", ".")
        code, report = self.audit("check", "--for-commit", target=package)
        self.assertEqual(code, 0, report["findings"])
        self.assertEqual(report["git"]["scope"], " spaced package")
        self.assertIn("module.py", report["git"]["staged_paths"])
        self.assertIn("README.md", report["documents"])

    def test_external_local_config_include_is_not_read(self):
        self.core()
        self.git("init", "-b", "main")
        outside = tempfile.TemporaryDirectory(prefix="project-init-include-outside-")
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "config"
        target.write_text('[remote "origin"]\nurl = https://example.invalid/OUTSIDE_INCLUDE_VALUE\n')
        with (self.root / ".git/config").open("a") as stream:
            stream.write("[include]\npath = " + str(target) + "\n")
        code, report = self.audit("check", "--for-commit")
        self.assertEqual(code, 1)
        self.assertFalse(report["git"]["valid"])
        self.assertFalse(report["scan"]["complete"])
        self.assertNotIn("OUTSIDE_INCLUDE_VALUE", json.dumps(report))

    def test_normal_linked_worktree_keeps_git_support_without_modification(self):
        self.core()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("add", ".")
        self.git("commit", "--no-gpg-sign", "-m", "Fixture baseline")
        temporary = tempfile.TemporaryDirectory(prefix="project-init-worktree-")
        self.addCleanup(temporary.cleanup)
        linked = Path(temporary.name) / "linked"
        self.git("worktree", "add", "-b", "review", str(linked))
        before = self.snapshot()
        code, report = self.audit("check", "--for-commit", target=linked)
        self.assertEqual(code, 0, report["findings"])
        self.assertTrue(report["git"]["valid"])
        self.assertEqual(report["git"]["root"], str(linked))
        self.assertEqual(report["git"]["branch"], "review")
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
