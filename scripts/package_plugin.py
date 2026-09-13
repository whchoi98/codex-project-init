#!/usr/bin/env python3
"""Build validated, reproducible plugin and standalone skill distributions."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import zipfile

if __package__:
    from .distribution import (
        DistributionError, PAYLOAD_TREES, PLUGIN_NAME, SKILL_NAME, SKILL_ROOT,
        source_snapshot,
    )
    from .validate_distribution import (
        ZIP_MODE, ZIP_TIMESTAMP, artifact_names, validate_distribution,
    )
else:
    from distribution import (
        DistributionError, PAYLOAD_TREES, PLUGIN_NAME, SKILL_NAME, SKILL_ROOT,
        source_snapshot,
    )
    from validate_distribution import (
        ZIP_MODE, ZIP_TIMESTAMP, artifact_names, validate_distribution,
    )


ROOT = Path(__file__).resolve().parents[1]


def _write_archive(payload, root_name, destination):
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9,
        allowZip64=False,
    ) as archive:
        for relative, contents in sorted(payload.items()):
            entry = zipfile.ZipInfo(root_name + "/" + relative, date_time=ZIP_TIMESTAMP)
            entry.create_system = 3
            entry.external_attr = ZIP_MODE
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, contents, compresslevel=9)
    destination.chmod(0o644)
    return {
        "file": destination.name,
        "files": len(payload),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


def _check_output_directory(output, source):
    try:
        relative = output.relative_to(source).as_posix()
    except ValueError:
        relative = None
    if relative == "." or (relative is not None and any(
        relative == tree or relative.startswith(tree + "/")
        for tree in (*PAYLOAD_TREES, ".codex-plugin", "skills")
    )):
        raise DistributionError("Distribution output must be outside the source payload roots")
    for path in reversed((output, *output.parents)):
        if os.path.lexists(path) and not stat.S_ISDIR(path.lstat().st_mode):
            raise DistributionError("Distribution output ancestors must be real directories")


def _publish(staged, output, backup, names, payload):
    """Replace the validated set; restore old bytes if any publication step fails."""
    existed = {}
    replaced = []
    made_output = not output.exists()
    try:
        output.mkdir(exist_ok=True)
        backup.mkdir()
        # Finish preflight/backups before replacing even the first artifact.
        for name in names:
            destination = output / name
            existed[name] = os.path.lexists(destination)
            if existed[name]:
                if not stat.S_ISREG(destination.lstat().st_mode):
                    raise DistributionError("Refusing to replace a linked or special distribution file")
                shutil.copy2(destination, backup / name, follow_symlinks=False)
        for name in names:
            os.replace(staged / name, output / name)
            replaced.append(name)
        validate_distribution(output, payload)
    except BaseException as failure:
        restoration_failed = False
        for name in reversed(replaced):
            try:
                if existed[name]:
                    os.replace(backup / name, output / name)
                else:
                    (output / name).unlink()
            except OSError:
                restoration_failed = True
        if made_output:
            try:
                output.rmdir()
            except OSError:
                pass
        if restoration_failed:
            error = DistributionError(
                "Output recovery failed; previous artifacts are retained in " + str(backup)
            )
            error.recovery_directory = backup
            raise error from failure
        raise


def build_distribution(source: Path, output: Path = None) -> dict:
    """Build one validated snapshot, leaving existing outputs intact on failure."""
    manifest, payload = source_snapshot(source)
    source = Path(source).resolve()
    output = Path(os.path.abspath(os.fspath(output or source / "dist")))
    _check_output_directory(output, source)
    workspace = None
    keep_workspace = False
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix=".codex-project-init-build-", dir=output.parent))
        staged = workspace / "artifacts"
        staged.mkdir()
        names = artifact_names(manifest["version"])
        prefix = SKILL_ROOT + "/"
        skill = {
            name[len(prefix):]: contents
            for name, contents in payload.items() if name.startswith(prefix)
        }
        report = {
            "version": manifest["version"],
            "artifacts": [
                _write_archive(payload, PLUGIN_NAME, staged / names[0]),
                _write_archive(skill, SKILL_NAME, staged / names[1]),
            ],
        }
        (staged / "manifest.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (staged / "manifest.json").chmod(0o644)
        validate_distribution(staged, payload)
        _publish(staged, output, workspace / "backups", (*names, "manifest.json"), payload)
        return report
    except DistributionError as error:
        keep_workspace = hasattr(error, "recovery_directory")
        raise
    except (OSError, zipfile.LargeZipFile):
        raise DistributionError("Unable to write or publish distribution files") from None
    finally:
        if workspace is not None and not keep_workspace:
            try:
                shutil.rmtree(workspace)
            except OSError:
                # Cleanup must neither mask a build error nor turn a verified
                # publication into a reported failure after replacing outputs.
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT, help="Plugin source directory")
    parser.add_argument("--output", type=Path, help="Output directory (default: SOURCE/dist)")
    args = parser.parse_args(argv)
    report = build_distribution(args.source, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DistributionError, OSError) as error:
        print("Packaging failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
