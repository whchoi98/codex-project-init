"""Exercise distributions in isolated source copies and temporary destinations."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Other agents may edit the real skill/installer during this suite.
        # Every build and mutation below operates on this independent snapshot.
        cls.baseline_temp = tempfile.TemporaryDirectory(prefix="packaging-baseline-")
        cls.addClassCleanup(cls.baseline_temp.cleanup)
        cls.baseline = Path(cls.baseline_temp.name) / "source"
        shutil.copytree(
            ROOT, cls.baseline, symlinks=True,
            ignore=shutil.ignore_patterns(
                ".git", "dist", "__pycache__", "*.pyc", ".venv", ".pytest_cache",
            ),
        )

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="packaging-test-")
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        # Archive names must not depend on the checkout directory name.
        self.source = self.temporary / "arbitrary-checkout-name"
        shutil.copytree(self.baseline, self.source, symlinks=True)
        self.output = self.source / "dist"

    def write(self, relative, content):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def command(self, script, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(self.source / "scripts" / script), *arguments],
            cwd=self.temporary, capture_output=True, text=True, timeout=30,
        )

    def build(self):
        return self.command("package_plugin.py")

    def good_build(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(
            report, json.loads((self.output / "manifest.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(report["version"], self.source_version())
        return report

    def source_version(self):
        path = self.source / ".codex-plugin/plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))["version"]

    def archive(self, kind="plugin", version=None):
        if version is None:
            version = self.source_version()
        name = (
            "codex-project-init-{}.zip" if kind == "plugin"
            else "project-init-skill-{}.zip"
        ).format(version)
        return self.output / name

    def snapshot(self, root):
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def minimal_skill(self, body=""):
        self.write(
            "skills/project-init/SKILL.md",
            "---\nname: project-init\ndescription: Prepare project documentation.\n"
            "---\n\n" + body,
        )

    def edit_manifest(self, edit):
        path = self.source / ".codex-plugin/plugin.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        edit(manifest)
        path.write_text(json.dumps(manifest), encoding="utf-8")

    def update_archive_checksum(self, kind="plugin"):
        path = self.output / "manifest.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        for artifact in report["artifacts"]:
            if artifact["file"] == self.archive(kind).name:
                artifact["sha256"] = hashlib.sha256(self.archive(kind).read_bytes()).hexdigest()
                with zipfile.ZipFile(self.archive(kind)) as archive:
                    artifact["files"] = len(archive.infolist())
        path.write_text(json.dumps(report), encoding="utf-8")

    def load_distribution(self):
        path = self.source / "scripts/distribution.py"
        self.assertTrue(path.is_file(), "The shared installer payload contract is missing")
        spec = importlib.util.spec_from_file_location("packaging_distribution", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_payload_excludes_local_files_credentials_and_build_debris(self):
        marker = "LOCAL_" + "PRIVATE_FIXTURE"
        unwanted = [
            "private-notes.txt", "unrelated-project/main.py", ".env", ".env.example",
            "credentials.json", ".aws/credentials", ".codex-plugin/local-settings.json",
            "skills/other-skill/SKILL.md", "scripts/.env.production",
            "scripts/credentials.json", "scripts/private.pem", "scripts/local.pyc",
            "scripts/application_default_credentials.json", "scripts/kubeconfig",
            "docs/service-account.json", "docs/local.tfstate",
            "scripts/__pycache__/cached.pyc", "scripts/.cache/local.txt",
            "docs/.ssh/id_ed25519", "docs/build/output.txt", "docs/secrets.yaml",
            "tests/.pytest_cache/state", "tests/.venv/settings.py",
            "skills/project-init/.env.local",
            "skills/project-init/references/credentials.txt",
            "skills/project-init/assets/private.key",
            "skills/project-init/scripts/__pycache__/leak.pyc",
        ]
        for path in unwanted:
            self.write(path, marker)
        self.good_build()
        with zipfile.ZipFile(self.archive()) as archive:
            members = set(archive.namelist())
            for relative in unwanted:
                self.assertFalse(
                    any(name.endswith("/" + relative) for name in members), relative,
                )
            for expected in (
                ".codex-plugin/plugin.json", "skills/project-init/SKILL.md",
                "skills/project-init/scripts/project_audit.py", "README.md", "LICENSE",
                "scripts/package_plugin.py", "Makefile", "tests/test_packaging.py",
                "docs/README.md",
            ):
                self.assertIn("codex-project-init/" + expected, members)
            self.assertTrue(all(name.startswith("codex-project-init/") for name in members))
            self.assertFalse(any(marker.encode("utf-8") in archive.read(name)
                                 for name in members))

    def native_catalogue(self):
        # The sandbox may expose the checkout's .agents as read-only. Mutation
        # tests own this disposable copy, not the source checkout's permissions.
        for relative in (".agents", ".agents/plugins", ".agents/plugins/marketplace.json"):
            path = self.source / relative
            if path.exists():
                path.chmod(stat.S_IMODE(path.stat().st_mode) | (0o700 if path.is_dir() else 0o600))
        return {
            "name": "codex-project-init",
            "interface": {"displayName": "Codex Project Init"},
            "plugins": [{
                "name": "codex-project-init",
                "source": {"source": "local", "path": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }],
        }

    def test_plugin_archive_preserves_a_resolvable_native_marketplace(self):
        catalogue = self.native_catalogue()
        self.write(".agents/plugins/marketplace.json", json.dumps(catalogue) + "\n")
        self.write(".agents/settings.json", '{"local_only": true}\n')
        self.good_build()
        with zipfile.ZipFile(self.archive()) as archive:
            name = "codex-project-init/.agents/plugins/marketplace.json"
            self.assertIn(name, archive.namelist())
            bundled = json.loads(archive.read(name))
            self.assertEqual(bundled, catalogue)
            plugin_root = "codex-project-init/" + bundled["plugins"][0]["source"]["path"][2:]
            manifest = json.loads(archive.read(plugin_root + ".codex-plugin/plugin.json"))
            self.assertEqual(manifest["name"], bundled["plugins"][0]["name"])
            self.assertNotIn("codex-project-init/.agents/settings.json", archive.namelist())
        with zipfile.ZipFile(self.archive("skill")) as archive:
            self.assertFalse(any("/.agents/" in name for name in archive.namelist()))

    def test_invalid_native_marketplace_cannot_replace_valid_distributions(self):
        for broken in ("outside", "missing", "wrong_plugin", "missing_policy",
                       "policy_type", "duplicate"):
            with self.subTest(broken=broken):
                catalogue = self.native_catalogue()
                self.write(".agents/plugins/marketplace.json", json.dumps(catalogue) + "\n")
                self.good_build()
                before = self.snapshot(self.output)
                if broken == "outside":
                    catalogue["plugins"][0]["source"]["path"] = "../outside"
                elif broken == "missing":
                    catalogue["plugins"][0]["source"]["path"] = "./missing"
                elif broken == "wrong_plugin":
                    catalogue["plugins"][0]["name"] = "some-other-plugin"
                elif broken == "missing_policy":
                    del catalogue["plugins"][0]["policy"]
                elif broken == "policy_type":
                    catalogue["plugins"][0]["policy"]["installation"] = []
                else:
                    catalogue["plugins"].append(dict(catalogue["plugins"][0]))
                self.write(".agents/plugins/marketplace.json", json.dumps(catalogue) + "\n")
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.snapshot(self.output), before)

    def test_prefixed_credential_filenames_are_excluded_from_both_payloads(self):
        names = (
            "client_secret.json", "local-credentials.json", "oauth-client-secrets.yaml",
            "team.credentials.toml", "PRODUCTION_CLIENT_SECRET.JSON",
        )
        for name in names:
            self.write("skills/project-init/references/" + name, '{"dummy": "example"}\n')
        # Credential terminology in ordinary maintained docs/code is not a
        # credential config file, and partial word matches are not filenames.
        retained = {
            "references/client-secret-format.md": "# Configuration format\n",
            "scripts/test_credential_format.py": "def check_format():\n    return True\n",
            "references/secretion.json": "{}\n",
        }
        for relative, contents in retained.items():
            self.write("skills/project-init/" + relative, contents)
        report = self.good_build()
        for artifact in report["artifacts"]:
            with zipfile.ZipFile(self.output / artifact["file"]) as archive:
                with self.subTest(archive=artifact["file"]):
                    members = archive.namelist()
                    for name in names:
                        self.assertFalse(any(item.endswith("/references/" + name)
                                             for item in members), name)
                    for relative in retained:
                        self.assertTrue(any(item.endswith("/" + relative) for item in members),
                                        relative)
        distribution = self.load_distribution()
        selected = distribution.payload_files(self.source)
        self.assertFalse(any(path.name in names for path in selected))

    def test_repeated_builds_ignore_source_times_and_permissions(self):
        self.good_build()
        before = self.snapshot(self.output)
        for path in self.source.rglob("*"):
            if self.output in path.parents or not path.is_file() or path.is_symlink():
                continue
            os.utime(path, (1712345678, 1712345678))
            path.chmod(0o777)
        self.good_build()
        self.assertEqual(self.snapshot(self.output), before)
        for archive_path, root_name in (
            (self.archive(), "codex-project-init/"),
            (self.archive("skill"), "project-init/"),
        ):
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                for member in archive.infolist():
                    self.assertTrue(member.filename.startswith(root_name))
                    self.assertEqual(member.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual(member.create_system, 3)
                    self.assertEqual(member.external_attr >> 16, stat.S_IFREG | 0o644)

    def test_plugin_manifest_is_the_version_authority(self):
        self.edit_manifest(lambda value: value.update(version="1.2.3-rc.1+fixture"))
        self.write("VERSION", "99.99.99\n")
        report = self.good_build()
        self.assertEqual(report["version"], "1.2.3-rc.1+fixture")
        self.assertEqual(
            {item["file"] for item in report["artifacts"]},
            {"codex-project-init-1.2.3-rc.1+fixture.zip",
             "project-init-skill-1.2.3-rc.1+fixture.zip"},
        )

    def test_changed_fixture_version_keeps_packaging_smoke_tests_working(self):
        self.edit_manifest(lambda value: value.update(version="0.1.1"))
        self.good_build()
        # These real tests exercise archive lookup and the other version
        # assertions. The selector excludes this test, so it cannot recurse.
        result = subprocess.run(
            [
                sys.executable, "-B", "-m", "unittest", "discover",
                "-s", "tests", "-p", "test_packaging.py",
                "-k", "both_extracted_payloads", "-k", "cleanup_failure",
                "-k", "packaging_and_validation", "-v",
            ],
            cwd=self.source, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_included_symlink_fails_without_replacing_good_outputs(self):
        self.good_build()
        before = self.snapshot(self.output)
        outside = self.temporary / "private.txt"
        outside.write_text("PRIVATE_OUTSIDE_VALUE", encoding="utf-8")
        link = self.source / "skills/project-init/references/linked.md"
        link.symlink_to(outside)
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PRIVATE_OUTSIDE_VALUE", result.stderr + result.stdout)
        self.assertEqual(self.snapshot(self.output), before)

    def test_included_directory_symlink_is_rejected(self):
        (self.source / "docs/linked").symlink_to(
            self.source / "skills/project-init/references", target_is_directory=True,
        )
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse(self.output.exists())

    def test_manifest_parent_symlink_is_rejected(self):
        metadata = self.source / ".codex-plugin"
        outside = self.temporary / "metadata"
        metadata.rename(outside)
        metadata.symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires a filesystem with FIFOs")
    def test_included_special_file_is_rejected_without_reading_it(self):
        os.mkfifo(self.source / "skills/project-init/references/stream.md")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_ignored_outside_payload_symlinks_are_not_followed(self):
        (self.source / "private-link").symlink_to(self.temporary, target_is_directory=True)
        self.good_build()
        with zipfile.ZipFile(self.archive()) as archive:
            self.assertFalse(any("private-link" in name for name in archive.namelist()))

    def test_invalid_metadata_leaves_good_artifacts_unchanged(self):
        self.good_build()
        before = self.snapshot(self.output)
        original = (self.source / ".codex-plugin/plugin.json").read_bytes()
        changes = [
            {"name": "another-plugin"}, {"version": "../../escape"},
            {"version": "01.2.3"}, {"description": ""},
            {"skills": "../outside"}, {"interface": []},
            {"author": {"name": ""}},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.write(".codex-plugin/plugin.json", original)
                self.edit_manifest(lambda value: value.update(change))
                result = self.build()
                self.assertNotEqual(result.returncode, 0, change)
                self.assertEqual(self.snapshot(self.output), before)
        self.assertFalse((self.temporary / "escape").exists())

    def test_missing_linked_skill_reference_is_rejected(self):
        self.minimal_skill("[Guide](references/not-shipped.md)\n")
        self.assertNotEqual(self.build().returncode, 0)

    def test_transitive_local_references_and_assets_must_be_self_contained(self):
        self.minimal_skill("[Guide](references/guide.md)\n")
        guide = self.write(
            "skills/project-init/references/guide.md",
            "[Asset](../assets/absent.svg)\n",
        )
        self.assertNotEqual(self.build().returncode, 0)
        guide.write_text("[Outside](../../../README.md)\n", encoding="utf-8")
        self.assertNotEqual(self.build().returncode, 0)

    def test_missing_bundled_script_is_rejected(self):
        (self.source / "skills/project-init/scripts/project_audit.py").unlink()
        self.assertNotEqual(self.build().returncode, 0)

    def test_imported_local_modules_must_be_in_the_payload_without_executing_them(self):
        self.write(
            "skills/project-init/scripts/project_audit.py",
            "from packaging_fixture.worker import run\n",
        )
        self.write("skills/project-init/scripts/packaging_fixture/__init__.py", "")
        self.write(
            "skills/project-init/scripts/packaging_fixture/worker.py",
            "from .missing import run\nraise RuntimeError('MUST_NOT_EXECUTE')\n",
        )
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.write(
            "skills/project-init/scripts/packaging_fixture/missing.py",
            "def run():\n    return None\n",
        )
        self.good_build()
        (self.source / "skills/project-init/scripts/packaging_fixture/worker.py").unlink()
        self.assertNotEqual(self.build().returncode, 0)

    def test_from_package_submodule_import_fails_when_the_submodule_is_missing(self):
        cases = (
            ("project_audit.py", "from packaging_probe import worker\n"),
            ("project_audit.py", "from packaging_probe import worker as renamed\n"),
            ("packaging_probe/consumer.py", "from . import worker\n"),
            ("packaging_probe/__init__.py", "from . import worker\n"),
        )
        for importer, contents in cases:
            with self.subTest(importer=importer, statement=contents):
                self.write("skills/project-init/scripts/packaging_probe/__init__.py", "")
                self.write("skills/project-init/scripts/project_audit.py", "")
                self.write("skills/project-init/scripts/" + importer, contents)
                worker = self.write(
                    "skills/project-init/scripts/packaging_probe/worker.py", "VALUE = 42\n",
                )
                self.good_build()
                before = self.snapshot(self.output)
                worker.unlink()
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(self.output), before)
                distribution = self.load_distribution()
                with self.assertRaises(distribution.DistributionError):
                    distribution.validate_source(self.source)
                with self.assertRaises(distribution.DistributionError):
                    distribution.payload_files(self.source)

    def test_from_imports_preserve_declared_symbols_and_reexports_without_execution(self):
        self.write(
            "skills/project-init/scripts/project_audit.py",
            "from packaging_probe import worker, Handler, first, annotated, paths\n"
            "from packaging_probe.api import run, Worker, SECOND\n",
        )
        self.write(
            "skills/project-init/scripts/packaging_probe/__init__.py",
            "from .api import run as worker\n"
            "import pathlib as paths\n"
            "class Handler:\n    pass\n"
            "first, second = (1, 2)\n"
            "annotated: int = 3\n"
            "raise RuntimeError('SOURCE_MUST_NOT_EXECUTE')\n",
        )
        self.write(
            "skills/project-init/scripts/packaging_probe/api.py",
            "def run():\n    return None\n"
            "class Worker:\n    pass\n"
            "SECOND = 2\n",
        )
        self.good_build()

    def test_imported_symbol_must_not_be_just_a_function_local_name(self):
        self.write(
            "skills/project-init/scripts/project_audit.py",
            "from packaging_probe import worker\n",
        )
        for contents in (
            "def create():\n    worker = 42\n    return worker\n",
            "class Container:\n    worker = 42\n",
            "worker: int\n",
        ):
            with self.subTest(contents=contents):
                self.write("skills/project-init/scripts/packaging_probe/__init__.py", contents)
                self.assertNotEqual(self.build().returncode, 0)

    def test_inline_script_commands_validate_only_the_script_path(self):
        self.minimal_skill(
            "Run `scripts/project_audit.py --help` or "
            "`scripts/project_audit.py inspect '../temporary project'`.\n"
            "Read `references/guide with spaces.md` and `scripts/helper with spaces.py`.\n"
        )
        self.write("skills/project-init/references/guide with spaces.md", "# Guide\n")
        self.write("skills/project-init/scripts/helper with spaces.py", "VALUE = 1\n")
        self.good_build()
        self.minimal_skill("Run `scripts/not-bundled.py --help`.\n")
        self.assertNotEqual(self.build().returncode, 0)

    def test_skill_metadata_validates_quoted_and_folded_scalars(self):
        self.write(
            "skills/project-init/SKILL.md",
            "---\ndescription: >-\n  Prepare repository docs\n  from actual source.\n"
            "name: 'project-init' # valid YAML comment\n---\n\n"
            "[Guide](<references/a(b).md> \"Local guide\")\n"
            "[Web](https://example.invalid/no-network)\n"
            "```markdown\n[Example](not-a-real-resource.md)\n```\n",
        )
        self.write("skills/project-init/references/a(b).md", "# A guide\n")
        self.good_build()
        self.write(
            "skills/project-init/SKILL.md",
            "---\nname: other-skill\ndescription: A description.\n---\n",
        )
        self.assertNotEqual(self.build().returncode, 0)

    def test_skill_interface_assets_are_checked_without_external_yaml(self):
        self.write(
            "skills/project-init/agents/openai.yaml",
            "interface:\n  display_name: Project Init\n"
            "  short_description: Prepare project docs\n"
            "  icon_small: ../README.md\n",
        )
        self.assertNotEqual(self.build().returncode, 0)
        self.write(
            "skills/project-init/agents/openai.yaml",
            "interface:\n  display_name: Project Init\n"
            "  short_description: Prepare project docs\n"
            "  icon_small: ./assets/icon.svg\n",
        )
        self.assertNotEqual(self.build().returncode, 0)
        self.write("skills/project-init/assets/icon.svg", "<svg/>")
        self.good_build()

    def test_shared_installer_contract_returns_safe_absolute_plugin_paths(self):
        self.write("local-secret.json", "PRIVATE_LOCAL")
        distribution = self.load_distribution()
        self.assertTrue(issubclass(distribution.DistributionError, ValueError))
        self.assertEqual(distribution.validate_source(self.source)["name"], "codex-project-init")
        paths = distribution.payload_files(self.source)
        self.assertIsInstance(paths, list)
        self.assertTrue(paths)
        for path in paths:
            self.assertIsInstance(path, Path)
            self.assertTrue(path.is_absolute())
            self.assertTrue(path.is_file())
            self.assertFalse(path.is_symlink())
            path.relative_to(self.source)
        relatives = [path.relative_to(self.source).as_posix() for path in paths]
        self.assertEqual(relatives, sorted(relatives))
        self.assertNotIn("local-secret.json", relatives)
        self.good_build()
        with zipfile.ZipFile(self.archive()) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {"codex-project-init/" + relative for relative in relatives},
            )
        link = self.source / "skills/project-init/assets/unsafe.md"
        link.symlink_to(self.source / "README.md")
        with self.assertRaises(distribution.DistributionError):
            distribution.payload_files(self.source)
        with self.assertRaises(distribution.DistributionError):
            distribution.validate_source(self.source)

    def test_archive_checksum_manifest_and_verifier_detect_tampering(self):
        report = self.good_build()
        for item in report["artifacts"]:
            path = self.output / item["file"]
            self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(item["files"], len(archive.infolist()))
        validator = self.source / "scripts/validate_distribution.py"
        self.assertTrue(validator.is_file(), "The offline distribution verifier is missing")
        result = self.command("validate_distribution.py")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        with self.archive().open("ab") as stream:
            stream.write(b"tampering")
        result = self.command("validate_distribution.py")
        self.assertNotEqual(result.returncode, 0)

    def test_manifest_and_archive_metadata_are_verified_even_with_updated_hashes(self):
        from scripts.validate_distribution import DistributionError, validate_distribution

        self.good_build()
        validator = self.source / "scripts/validate_distribution.py"
        self.assertTrue(validator.is_file(), "The offline distribution verifier is missing")
        with zipfile.ZipFile(self.archive()) as original:
            files = {item.filename: original.read(item) for item in original.infolist()}
        files["codex-project-init/../../outside.txt"] = b"UNSAFE"
        # Keep every other property canonical so the path check is exercised.
        with zipfile.ZipFile(self.archive(), "w") as archive:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = (stat.S_IFREG | 0o644) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data, compresslevel=9)
        self.update_archive_checksum()
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)
        self.assertFalse((self.temporary / "outside.txt").exists())

    def test_local_zip_timestamps_must_match_canonical_directory_metadata(self):
        from scripts.validate_distribution import DistributionError, validate_distribution

        self.good_build()
        data = bytearray(self.archive().read_bytes())
        struct.pack_into("<H", data, 10, 1234)  # First local file header's DOS time.
        self.archive().write_bytes(data)
        self.update_archive_checksum()
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)

    def test_corrupt_deflate_data_raises_distribution_error(self):
        from scripts.validate_distribution import DistributionError, validate_distribution

        self.good_build()
        data = bytearray(self.archive().read_bytes())
        filename_length, extra_length = struct.unpack_from("<HH", data, 26)
        compressed_offset = 30 + filename_length + extra_length
        data[compressed_offset] = 0xFF  # Invalid DEFLATE block type.
        self.archive().write_bytes(data)
        self.update_archive_checksum()
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)

    def test_zip_names_cannot_hide_suffixes_after_a_null_byte(self):
        from scripts.validate_distribution import DistributionError, validate_distribution

        self.write("docs/guide.md-hidden", "# Guide\n")
        self.good_build()
        data = self.archive().read_bytes()
        data = data.replace(b"docs/guide.md-hidden", b"docs/guide.md\x00hidden")
        self.archive().write_bytes(data)
        self.update_archive_checksum()
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)

    def test_offline_verifier_checks_manifest_version_and_skill_agreement(self):
        from scripts.validate_distribution import DistributionError, validate_distribution

        self.good_build()
        validate_distribution(self.output)
        manifest_path = self.output / "manifest.json"
        original_manifest = manifest_path.read_bytes()
        report = json.loads(original_manifest)
        report["version"] = "9.9.9"
        manifest_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)
        manifest_path.write_bytes(original_manifest)
        with zipfile.ZipFile(self.archive("skill")) as archive:
            files = {item.filename: (item, archive.read(item)) for item in archive.infolist()}
        entry, data = files["project-init/SKILL.md"]
        files[entry.filename] = (entry, data + b"\nDifferent standalone skill.\n")
        with zipfile.ZipFile(self.archive("skill"), "w") as archive:
            for entry, data in files.values():
                archive.writestr(entry, data, compresslevel=9)
        self.update_archive_checksum("skill")
        with self.assertRaises(DistributionError):
            validate_distribution(self.output)

    def test_failed_second_archive_write_preserves_previous_artifacts(self):
        from scripts import package_plugin

        self.good_build()
        before = self.snapshot(self.output)
        self.write("docs/new.md", "# New source bytes\n")
        write_archive = package_plugin._write_archive

        def fail_skill(payload, root_name, destination):
            if root_name == "project-init":
                destination.write_bytes(b"PARTIAL_ARCHIVE")
                raise OSError("simulated write failure")
            return write_archive(payload, root_name, destination)

        with mock.patch.object(package_plugin, "_write_archive", side_effect=fail_skill):
            with self.assertRaises(package_plugin.DistributionError):
                package_plugin.build_distribution(self.source, self.output)
        self.assertEqual(self.snapshot(self.output), before)
        self.assertFalse(list(self.source.glob(".codex-project-init-build-*")))

    def test_failed_second_archive_publication_restores_previous_artifacts(self):
        from scripts import package_plugin

        self.good_build()
        before = self.snapshot(self.output)
        self.write("docs/new.md", "# New source bytes\n")
        replace = package_plugin.os.replace

        def fail_skill(source, destination):
            if (Path(source).parent.name == "artifacts"
                    and Path(destination).name == self.archive("skill").name):
                raise OSError("simulated publication failure")
            return replace(source, destination)

        with mock.patch.object(package_plugin.os, "replace", side_effect=fail_skill):
            with self.assertRaises(package_plugin.DistributionError):
                package_plugin.build_distribution(self.source, self.output)
        self.assertEqual(self.snapshot(self.output), before)
        self.assertFalse(list(self.source.glob(".codex-project-init-build-*")))

    def test_failed_published_validation_restores_previous_artifacts(self):
        from scripts import package_plugin

        self.good_build()
        before = self.snapshot(self.output)
        self.write("docs/new.md", "# New source bytes\n")
        validate = package_plugin.validate_distribution

        def fail_published(output, expected_payload=None):
            if Path(output) == self.output:
                raise package_plugin.DistributionError("simulated verification failure")
            return validate(output, expected_payload)

        with mock.patch.object(package_plugin, "validate_distribution", side_effect=fail_published):
            with self.assertRaises(package_plugin.DistributionError):
                package_plugin.build_distribution(self.source, self.output)
        self.assertEqual(self.snapshot(self.output), before)

    def test_cleanup_failure_does_not_report_failure_after_verified_publication(self):
        from scripts import package_plugin

        self.good_build()
        self.write("docs/new.md", "# New source bytes\n")
        with mock.patch.object(package_plugin.shutil, "rmtree", side_effect=OSError("busy directory")):
            report = package_plugin.build_distribution(self.source, self.output)
        self.assertEqual(report["version"], self.source_version())
        with zipfile.ZipFile(self.archive()) as archive:
            self.assertEqual(archive.read("codex-project-init/docs/new.md"), b"# New source bytes\n")
        result = self.command("validate_distribution.py")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_symlinked_output_directory_or_file_cannot_overwrite_external_data(self):
        outside = self.temporary / "external"
        outside.mkdir()
        protected = outside / self.archive().name
        protected.write_bytes(b"PROTECTED")
        self.output.symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.build().returncode, 0)
        self.assertEqual(protected.read_bytes(), b"PROTECTED")
        self.output.unlink()
        self.output.mkdir()
        self.archive().symlink_to(protected)
        self.assertNotEqual(self.build().returncode, 0)
        self.assertEqual(protected.read_bytes(), b"PROTECTED")
        self.assertTrue(self.archive().is_symlink())

    def test_packaging_and_validation_need_only_the_standard_library(self):
        for script, arguments in (
            ("package_plugin.py", ()),
            ("validate_distribution.py", ()),
            ("validate_distribution.py", ("--source-only",)),
        ):
            result = subprocess.run(
                [sys.executable, "-S", "-B", str(self.source / "scripts" / script), *arguments],
                cwd=self.temporary, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)["version"], self.source_version())

    def test_both_extracted_payloads_run_real_auditor_without_changing_target(self):
        self.good_build()
        target = self.temporary / "target"
        target.mkdir()
        (target / "README.md").write_text("# Temporary project\n", encoding="utf-8")
        (target / "package.json").write_text(
            json.dumps({"name": "packaging-smoke", "scripts": {"test": "touch should-not-run"}}),
            encoding="utf-8",
        )
        environment = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        subprocess.run(
            ["git", "-c", "init.defaultBranch=main", "init", "--quiet", "--template=", str(target)],
            env=environment, capture_output=True, check=True, timeout=15,
        )
        before = self.snapshot(target)
        skill_payloads = []
        for kind, relative in (
            ("plugin", "codex-project-init/skills/project-init"),
            ("skill", "project-init"),
        ):
            extraction = self.temporary / ("extracted-" + kind)
            with zipfile.ZipFile(self.archive(kind)) as archive:
                archive.extractall(extraction)
            skill = extraction / relative
            skill_payloads.append(self.snapshot(skill))
            result = subprocess.run(
                [sys.executable, "-B", str(skill / "scripts/project_audit.py"),
                 "inspect", str(target)],
                cwd=self.temporary, env=environment, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["project"]["name"], "packaging-smoke")
            self.assertTrue(report["git"]["valid"])
            self.assertEqual(self.snapshot(target), before)
        self.assertEqual(skill_payloads[0], skill_payloads[1])


if __name__ == "__main__":
    unittest.main()
