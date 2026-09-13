"""Git observations scoped to the requested target, with executable filters off."""

from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import urlsplit, urlunsplit

from .filesystem import MAX_BYTES, FileNotRead, finding, safe_read

SECRET_RULES = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
}
MAX_GIT_OUTPUT = 8 * 1024 * 1024
MAX_METADATA_ENTRIES = 50000


def _metadata_directory(path):
    """Check pointer destinations before resolving away a filesystem symlink."""
    for component in (path, *path.parents):
        if component.is_symlink():
            raise FileNotRead("git_external_metadata")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotRead("git_metadata_not_read")
    return resolved


def metadata_error(root):
    """Validate Git's local metadata before Git can open linked config/index files.

    Git worktree/submodule pointer files are supported. Filesystem symlinks and
    config includes are not delegated to Git, which would follow them outside
    the file-reader boundary.
    """
    try:
        git_dir = None
        for directory in (root, *root.parents):
            marker = directory / ".git"
            if marker.is_symlink():
                return "git_external_metadata"
            if not marker.exists():
                continue
            if marker.is_dir():
                git_dir = _metadata_directory(marker)
            elif marker.is_file():
                raw = safe_read(directory, ".git").rstrip(b"\r\n")
                if not raw.startswith(b"gitdir: ") or b"\0" in raw or b"\n" in raw:
                    return "git_metadata_not_read"
                git_dir = _metadata_directory(directory / os.fsdecode(raw[8:]))
            else:
                return "git_metadata_not_read"
            break
        if git_dir is None:
            return None
        common = git_dir / "commondir"
        if common.is_symlink():
            return "git_external_metadata"
        roots = [git_dir]
        if common.exists():
            value = safe_read(git_dir, "commondir").rstrip(b"\r\n")
            if not value or b"\0" in value or b"\n" in value:
                return "git_metadata_not_read"
            common_dir = _metadata_directory(git_dir / os.fsdecode(value))
            roots = [common_dir] if git_dir.is_relative_to(common_dir) else [common_dir, git_dir]
        stack, seen, count = list(roots), set(), 0
        while stack:
            directory = stack.pop()
            if directory in seen:
                continue
            seen.add(directory)
            with os.scandir(directory) as entries:
                for entry in entries:
                    count += 1
                    if count > MAX_METADATA_ENTRIES:
                        return "git_metadata_truncated"
                    mode = entry.stat(follow_symlinks=False).st_mode
                    if stat.S_ISLNK(mode):
                        return "git_external_metadata"
                    path = Path(entry.path)
                    if stat.S_ISDIR(mode):
                        stack.append(path)
                    elif not stat.S_ISREG(mode):
                        return "git_metadata_not_read"
                    elif entry.name in {"config", "config.worktree"}:
                        content = safe_read(directory, entry.name)
                        # Do not ask Git to expand local includes. The full Git
                        # include language (conditional paths, interpolation)
                        # is not a project-local file-reference contract.
                        if re.search(rb"(?im)^\s*\[\s*include(?:if)?(?:\s|\]|\.)", content):
                            return "git_config_include_unsupported"
    except (OSError, RuntimeError, ValueError):
        return "git_metadata_not_read"
    return None


def public_text(value):
    if not isinstance(value, str):
        return None
    data = value.encode("utf-8", "replace")
    for pattern in SECRET_RULES.values():
        data = pattern.sub(b"[redacted]", data)
    return data.decode("utf-8", "replace")


def public_remote(value):
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme in {"http", "https", "ssh", "git"} and parsed.netloc:
            return public_text(urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1],
                                          parsed.path, "", "")))
        match = re.fullmatch(r"[^/@\s]+@([^:\s]+):(.+)", value)
        if match:
            return public_text("ssh://" + match[1] + "/"
                               + match[2].split("?", 1)[0].split("#", 1)[0])
    except ValueError:
        pass
    return "(local or nonstandard remote configured)"


class Repository:
    def __init__(self, root):
        self.root = root
        self.failures = []
        self.prefix = ""
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update({
            "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_ATTR_NOSYSTEM": "1",
        })
        self.command = [
            "git", "--no-optional-locks", "--literal-pathspecs",
            "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
            "-c", "core.hooksPath=" + os.devnull,
            "-c", "core.excludesFile=" + os.devnull,
            "-c", "core.attributesFile=" + os.devnull,
            "-c", "maintenance.auto=false", "-c", "gc.auto=0",
            "-c", "protocol.allow=never", "-C", str(root),
        ]
        boundary_error = metadata_error(root)
        if boundary_error:
            self.failures.append(boundary_error)
            self.valid = False
            return
        # --no-ext-diff/--no-textconv do not disable clean/process filters used
        # by status and worktree diff. Enumerate names only, never config values.
        code, keys = self.run("config", "--null", "--name-only", "--get-regexp",
                              r"^filter\..*\.(clean|smudge|process|required)$")
        if code not in (0, 1):
            self.failures.append("git_configuration_unavailable")
        overrides = []
        for prefix in sorted({key.rsplit(b".", 1)[0] for key in keys.split(b"\0") if key}):
            name = os.fsdecode(prefix)
            for suffix, value in (("clean", ""), ("smudge", ""), ("process", ""),
                                  ("required", "false")):
                overrides.append((name + "." + suffix, value))
        # Git -c splits on the first '='; valid filter subsection names can
        # themselves contain '='. Separate environment keys/values avoid that.
        self.env["GIT_CONFIG_COUNT"] = str(len(overrides))
        for index, (key, value) in enumerate(overrides):
            self.env["GIT_CONFIG_KEY_" + str(index)] = key
            self.env["GIT_CONFIG_VALUE_" + str(index)] = value
        for key, value in overrides:
            code, actual = self.run("config", "--null", "--get", key)
            if code or actual != value.encode() + b"\0":
                self.failures.append("git_filter_override_failed")
                self.valid = False
                return
        self.valid = self.text("rev-parse", "--is-inside-work-tree") == "true"
        if self.valid and self.failures:
            # A failed config inventory cannot prove that filters were disabled.
            self.valid = False
        if self.valid:
            self.prefix = self.text("rev-parse", "--show-prefix") or ""

    def run(self, *args):
        try:
            # Git may emit a large diff or object. A private temporary stream
            # bounds memory and keeps raw content out of logs and the target.
            with tempfile.TemporaryFile() as output:
                result = subprocess.run(
                    [*self.command, *args], stdout=output, stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL, timeout=5, env=self.env,
                )
                if output.tell() > MAX_GIT_OUTPUT:
                    return 2, b""
                output.seek(0)
                return result.returncode, output.read(MAX_GIT_OUTPUT)
        except (OSError, subprocess.TimeoutExpired):
            return 2, b""

    def text(self, *args):
        code, output = self.run(*args)
        return os.fsdecode(output).rstrip("\r\n") if code == 0 else None

    def names(self, *args):
        code, output = self.run(*args)
        if code:
            return None
        return [os.fsdecode(path) for path in output.split(b"\0") if path]

    def candidates(self):
        if not self.valid:
            return None
        names = self.names("ls-files", "--cached", "--others", "--exclude-standard",
                           "--full-name", "-z", "--", ".")
        if names is None:
            self.failures.append("git_inventory_unavailable")
            return None
        return [name[len(self.prefix):] for name in names if name.startswith(self.prefix)]

    def staged_names(self, diff_filter=None):
        args = ["diff", "--cached", "--name-only", "--relative", "--no-renames",
                "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", "-z"]
        if diff_filter:
            args.append("--diff-filter=" + diff_filter)
        return self.names(*args, "--", ".")

    def info(self):
        result = {
            "valid": self.valid, "root": None, "scope": self.prefix.rstrip("/"),
            "branch": None, "upstream": None, "remote": None, "dirty": None,
            "staged_paths": [],
        }
        if not self.valid:
            return result
        result.update({
            "root": self.text("rev-parse", "--show-toplevel"),
            "branch": public_text(self.text("symbolic-ref", "--quiet", "--short", "HEAD")
                                 or self.text("rev-parse", "--short", "HEAD")),
            "upstream": public_text(self.text("rev-parse", "--abbrev-ref",
                                            "--symbolic-full-name", "@{u}")),
            "remote": public_remote(self.text("remote", "get-url", "origin")),
        })
        code, status = self.run("status", "--porcelain=v1", "-z",
                                "--untracked-files=normal", "--ignore-submodules=all",
                                "--", ".")
        if code:
            self.failures.append("git_status_unavailable")
        else:
            result["dirty"] = bool(status)
        names = self.staged_names()
        if names is None:
            self.failures.append("staged_paths_unavailable")
        else:
            result["staged_paths"] = sorted(set(names))
        return result

    def preflight(self):
        issues = []
        for cached in (False, True):
            args = ["diff", "--check", "--no-ext-diff", "--no-textconv",
                    "--ignore-submodules=all"]
            if cached:
                args.append("--cached")
            code, _ = self.run(*args, "--", ".")
            if code:
                issues.append(finding(
                    "git_diff_check", ".",
                    ("Staged" if cached else "Working-tree")
                    + " whitespace/conflict check failed; review the scoped diff.",
                ))
        names = self.staged_names("ACMR")
        code, entries = self.run("ls-files", "--stage", "--full-name", "-z", "--", ".")
        if code or names is None:
            return issues + [finding("staged_scan_failed", ".", "Could not read the scoped index.")]
        blobs = {}
        for record in entries.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, oid, stage = metadata.split()
            path = os.fsdecode(raw_path)
            if not path.startswith(self.prefix):
                continue
            name = path[len(self.prefix):]
            if stage != b"0":
                issues.append(finding("unmerged_index", name, "Resolve the index conflict before committing."))
            else:
                blobs[name] = (mode, oid.decode("ascii"))
        if not self.staged_names():
            issues.append(finding("no_staged_changes", ".", "No changes are staged in this target.", "warning"))
        for name in names:
            base = Path(name).name
            example = base.endswith((".example", ".sample", ".template"))
            if ((base == ".env" or base.startswith(".env.")) and not example
                    or base in {"id_rsa", "id_ed25519", "credentials.json", ".credentials.json"}):
                issues.append(finding("staged_credential_file", name,
                                      "Review the staged credential-oriented file."))
            entry = blobs.get(name)
            if entry is None:
                issues.append(finding("staged_scan_failed", name, "No stage-zero blob is available."))
                continue
            mode, oid = entry
            if mode == b"160000":
                issues.append(finding("staged_scan_skipped", name,
                                      "Submodule content is outside this scan.", "warning"))
                continue
            size = self.text("cat-file", "-s", oid)
            if size is None or not size.isdigit():
                issues.append(finding("staged_scan_failed", name, "Could not read the staged blob size."))
                continue
            if int(size) > MAX_BYTES:
                issues.append(finding("staged_scan_skipped", name, "Blob exceeds the scan size limit.", "warning"))
                continue
            code, content = self.run("cat-file", "blob", oid)
            if code or len(content) > MAX_BYTES:
                issues.append(finding("staged_scan_failed", name, "Could not read the bounded staged blob."))
                continue
            if b"\0" in content:
                issues.append(finding("staged_scan_skipped", name, "Binary blob was not scanned for text indicators.", "warning"))
                continue
            for rule, pattern in SECRET_RULES.items():
                if pattern.search(content):
                    issues.append(finding("staged_secret", name, "Possible secret indicator: " + rule))
        return issues
