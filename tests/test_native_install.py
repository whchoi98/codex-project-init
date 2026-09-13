"""Exercise the distributed catalogue with a real CLI in a disposable profile."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from scripts.package_plugin import build_distribution


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    os.environ.get("PROJECT_INIT_REAL_INTEGRATION") == "1",
    "Set PROJECT_INIT_REAL_INTEGRATION=1 for optional installed Codex trials.",
)
class NativePluginInstallationTests(unittest.TestCase):
    def test_distributed_catalogue_installs_complete_plugin_and_reinstalls_updates(self):
        executable = shutil.which(os.environ.get("PROJECT_INIT_REAL_CODEX", "codex"))
        if executable is None:
            self.skipTest("A Codex CLI with plugin support is not installed.")
        with tempfile.TemporaryDirectory(prefix="native-plugin-install-") as temporary:
            trial = Path(temporary).resolve()
            output = trial / "dist"
            report = build_distribution(ROOT, output)
            archive = output / ("codex-project-init-" + report["version"] + ".zip")
            with zipfile.ZipFile(archive) as stream:
                stream.extractall(trial / "source")
            source = trial / "source/codex-project-init"
            profile = trial / "profile"
            codex_state = profile / ".codex"
            codex_state.mkdir(parents=True)
            environment = {
                key: os.environ[key]
                for key in ("PATH", "SYSTEMROOT", "LANG", "TMPDIR")
                if key in os.environ
            }
            environment.update({
                "HOME": str(profile),
                "CODEX_HOME": str(codex_state),
                "XDG_CONFIG_HOME": str(profile / ".config"),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
            })

            def command(*arguments):
                completed = subprocess.run(
                    [executable, *arguments], cwd=trial, env=environment,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(
                    completed.returncode, 0, completed.stderr + completed.stdout,
                )

            def snapshot(path):
                return {
                    item.relative_to(path).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                    for item in path.rglob("*") if item.is_file() and not item.is_symlink()
                }

            original = snapshot(source)
            command("plugin", "marketplace", "add", str(source))
            command("plugin", "add", "codex-project-init@codex-project-init")
            installed_entries = [
                path for path in profile.rglob("SKILL.md")
                if path.parent.name == "project-init"
            ]
            self.assertEqual(len(installed_entries), 1)
            installed_skill = installed_entries[0].parent
            source_skill = source / "skills/project-init"
            self.assertEqual(snapshot(installed_skill), snapshot(source_skill))
            self.assertEqual(snapshot(source), original)

            target = trial / "target"
            target.mkdir()
            (target / "README.md").write_text("# Native installation smoke project\n")
            target_before = snapshot(target)
            audit = subprocess.run(
                [sys.executable, str(installed_skill / "scripts/project_audit.py"),
                 "check", str(target), "--profile", "existing"],
                cwd=trial, env=environment, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(audit.returncode, 0, audit.stderr + audit.stdout)
            self.assertTrue(json.loads(audit.stdout)["scan"]["complete"])
            self.assertEqual(snapshot(target), target_before)

            # Our update instructions rely on re-adding this catalogue entry
            # refreshing its local source even when the version is unchanged.
            entrypoint = source_skill / "SKILL.md"
            entrypoint.write_bytes(entrypoint.read_bytes() + b"\nUpdated installation fixture.\n")
            command("plugin", "add", "codex-project-init@codex-project-init")
            self.assertEqual(snapshot(installed_skill), snapshot(source_skill))


if __name__ == "__main__":
    unittest.main()
