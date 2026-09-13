#!/usr/bin/env python3
"""Validate source metadata and both distribution archives without Codex/PyYAML."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import stat
import struct
import sys
import zipfile
import zlib

if __package__:
    from .distribution import (
        DistributionError, PLUGIN_NAME, SEMVER, SKILL_NAME, SKILL_ROOT,
        is_payload_path, json_object, read_regular, source_snapshot, validate_payload,
    )
else:
    from distribution import (
        DistributionError, PLUGIN_NAME, SEMVER, SKILL_NAME, SKILL_ROOT,
        is_payload_path, json_object, read_regular, source_snapshot, validate_payload,
    )


ROOT = Path(__file__).resolve().parents[1]
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = (stat.S_IFREG | 0o644) << 16
ZIP_DOS_TIME = (ZIP_TIMESTAMP[3] << 11) | (ZIP_TIMESTAMP[4] << 5) | (ZIP_TIMESTAMP[5] // 2)
ZIP_DOS_DATE = ((ZIP_TIMESTAMP[0] - 1980) << 9) | (ZIP_TIMESTAMP[1] << 5) | ZIP_TIMESTAMP[2]


def artifact_names(version):
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise DistributionError("Distribution version must be strict semver")
    return (
        PLUGIN_NAME + "-" + version + ".zip",
        SKILL_NAME + "-skill-" + version + ".zip",
    )


def _archive_payload(data, root_name):
    """Check both ZIP metadata and extracted bytes without filesystem extraction."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if not members or names != sorted(names) or len(names) != len(set(names)):
                raise DistributionError("ZIP entries must be unique and sorted")
            if archive.comment or len(data) < 22:
                raise DistributionError("ZIP must not contain an archive comment")
            end = struct.unpack("<4s4H2LH", data[-22:])
            if (end[0] != b"PK\x05\x06" or end[1:3] != (0, 0)
                    or end[3:5] != (len(members), len(members))
                    or end[5] + end[6] != len(data) - 22 or end[7] != 0
                    or end[6] != archive.start_dir):
                raise DistributionError("ZIP has non-canonical or trailing records")
            payload = {}
            offset = 0
            for member in members:
                prefix = root_name + "/"
                if member.orig_filename != member.filename:
                    raise DistributionError("ZIP contains a truncated or ambiguous file name")
                if not member.filename.startswith(prefix):
                    raise DistributionError("ZIP has the wrong top-level directory")
                relative = member.filename[len(prefix):]
                plugin_relative = (
                    relative if root_name == PLUGIN_NAME else SKILL_ROOT + "/" + relative
                )
                if not is_payload_path(plugin_relative):
                    raise DistributionError("ZIP includes a file outside the explicit payload")
                if (member.is_dir() or member.create_system != 3
                        or member.external_attr != ZIP_MODE
                        or member.date_time != ZIP_TIMESTAMP
                        or member.compress_type != zipfile.ZIP_DEFLATED
                        or member.extra or member.comment or member.flag_bits & ~0x800):
                    raise DistributionError("ZIP contains unsafe or non-deterministic file metadata")
                if member.header_offset != offset:
                    raise DistributionError("ZIP contains unexpected data between entries")
                local = struct.unpack_from("<4s5H3L2H", data, offset)
                if (local[0] != b"PK\x03\x04" or local[2] != member.flag_bits
                        or local[3] != member.compress_type or local[6] != member.CRC
                        or local[4:6] != (ZIP_DOS_TIME, ZIP_DOS_DATE)
                        or local[7] != member.compress_size or local[8] != member.file_size
                        or local[10] != 0):
                    raise DistributionError("ZIP local headers do not match the directory")
                offset += 30 + local[9] + local[10] + member.compress_size
                contents = archive.read(member)  # Also verifies local names and CRCs.
                if len(contents) != member.file_size:
                    raise DistributionError("ZIP file length does not match its metadata")
                payload[relative] = contents
            if offset != archive.start_dir:
                raise DistributionError("ZIP contains data outside its payload")
            return payload
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, struct.error, EOFError, zlib.error):
        raise DistributionError("Unreadable or corrupt ZIP archive") from None


def validate_distribution(output: Path, expected_payload=None) -> dict:
    """Verify manifest/checksums, safe ZIPs and identical standalone skill bytes.

    Pass a captured source payload to additionally detect stale distributions.
    Without one this validates the distribution entirely offline.
    """
    output = Path(output).absolute()
    try:
        if not stat.S_ISDIR(output.lstat().st_mode):
            raise DistributionError("Distribution directory must not be a symlink")
    except OSError:
        raise DistributionError("Distribution directory is missing or unreadable") from None
    report = json_object(read_regular(output, "manifest.json"), "manifest.json")
    names = artifact_names(report.get("version"))
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or any(not isinstance(item, dict) for item in artifacts):
        raise DistributionError("manifest.json artifacts must be an array of objects")
    if (any(not isinstance(item.get("file"), str) for item in artifacts)
            or {item["file"] for item in artifacts} != set(names)
            or len(artifacts) != len(names)):
        raise DistributionError("manifest.json must identify exactly the plugin and standalone ZIPs")
    archives = {}
    for item in artifacts:
        data = read_regular(output, item["file"])
        if item.get("sha256") != hashlib.sha256(data).hexdigest():
            raise DistributionError("Archive checksum does not match manifest.json: " + item["file"])
        root_name = PLUGIN_NAME if item["file"] == names[0] else SKILL_NAME
        payload = _archive_payload(data, root_name)
        if type(item.get("files")) is not int or item["files"] != len(payload):
            raise DistributionError("Archive file total does not match manifest.json")
        archives[root_name] = payload
    plugin = archives[PLUGIN_NAME]
    manifest = validate_payload(plugin)
    if manifest["version"] != report["version"]:
        raise DistributionError("Distribution version differs from the bundled plugin manifest")
    skill_prefix = SKILL_ROOT + "/"
    expected_skill = {
        name[len(skill_prefix):]: data
        for name, data in plugin.items() if name.startswith(skill_prefix)
    }
    if archives[SKILL_NAME] != expected_skill:
        raise DistributionError("Standalone skill differs from the plugin's skill payload")
    if expected_payload is not None and plugin != expected_payload:
        raise DistributionError("Distribution contents do not match the validated source")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT, help="Plugin source directory")
    parser.add_argument("--dist", type=Path, help="Distribution directory (default: SOURCE/dist)")
    parser.add_argument("--source-only", action="store_true", help="Validate source without archives")
    args = parser.parse_args(argv)
    manifest, payload = source_snapshot(args.source)
    if args.source_only:
        report = {"name": manifest["name"], "version": manifest["version"], "source_valid": True}
    else:
        report = validate_distribution(args.dist or args.source / "dist", payload)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DistributionError, OSError) as error:
        print("Distribution validation failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
