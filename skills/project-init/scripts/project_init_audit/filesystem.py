"""Bounded target-local file access; never read special files."""

from __future__ import annotations

import os
from pathlib import Path
import stat

MAX_FILES = 5000
MAX_BYTES = 1024 * 1024
DIRECTORY_OPEN = os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW")
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", ".nuxt", "dist", "build", "target",
}


class FileNotRead(ValueError):
    """An expected boundary or filesystem limitation, without file contents."""


def finding(code, path, message, severity="error"):
    return {"code": code, "path": str(path), "message": message, "severity": severity}


def local_path(root, relative):
    """Resolve only to check containment. Do not open external targets."""
    try:
        path = (root / relative).resolve()
    except (OSError, RuntimeError, ValueError):
        raise FileNotRead("unresolvable_path") from None
    if not path.is_relative_to(root):
        raise FileNotRead("external_symlink")
    return path


def regular_path(root, relative):
    path = local_path(root, relative)
    try:
        mode = path.stat().st_mode
    except OSError:
        raise FileNotRead("unreadable_path") from None
    if not stat.S_ISREG(mode):
        raise FileNotRead("special_file")
    return path


def safe_read(root, relative):
    """Read a bounded regular file, anchoring parent lookups where supported."""
    path = regular_path(root, relative)
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        expected = path.stat()
        if DIRECTORY_OPEN:
            directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            parent = os.open(root, directory_flags)
            try:
                parts = path.relative_to(root).parts
                for part in parts[:-1]:
                    child = os.open(part, directory_flags, dir_fd=parent)
                    os.close(parent)
                    parent = child
                fd = os.open(parts[-1], flags, dir_fd=parent)
            finally:
                os.close(parent)
        else:
            fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise FileNotRead("special_file")
            if (info.st_dev, info.st_ino) != (expected.st_dev, expected.st_ino):
                raise FileNotRead("file_changed_during_scan")
            if info.st_size > MAX_BYTES:
                raise FileNotRead("file_too_large")
            content = stream.read(MAX_BYTES + 1)
    except OSError:
        raise FileNotRead("unreadable_path") from None
    if len(content) > MAX_BYTES:
        raise FileNotRead("file_too_large")
    return content


class Inventory:
    def __init__(self, root, candidates=None):
        self.root = root
        self.files = []
        self.skipped = []
        self.excluded = []
        self.truncated = False
        self.candidates = set(candidates) if candidates is not None else None
        self._seen = 0

    def skip(self, path, reason):
        record = {"path": str(path), "reason": reason}
        if record not in self.skipped:
            self.skipped.append(record)
        if reason == "external_symlink" and str(path) not in self.excluded:
            self.excluded.append(str(path))

    def _visit(self, directory):
        try:
            with os.scandir(directory) as entries:
                # Bound allocation even when one directory has excessive entries.
                names = []
                for entry in entries:
                    if len(names) >= MAX_FILES + 1:
                        self.truncated = True
                        break
                    names.append(entry.name)
        except OSError:
            self.skip(directory.relative_to(self.root).as_posix(), "unreadable_directory")
            return
        for name in sorted(names):
            if self._seen >= MAX_FILES:
                self.truncated = True
                return
            path = directory / name
            relative = path.relative_to(self.root).as_posix()
            if name in SKIP_DIRS:
                continue
            if self.candidates is not None and not (
                relative in self.candidates or any(p.startswith(relative + "/")
                                                  for p in self.candidates)
            ):
                continue
            self._seen += 1
            try:
                resolved = local_path(self.root, relative)
                mode = resolved.stat().st_mode
            except (FileNotRead, OSError) as error:
                self.skip(relative, str(error) if isinstance(error, FileNotRead)
                          else "unreadable_path")
                continue
            if stat.S_ISDIR(mode):
                if path.is_symlink():
                    self.skip(relative, "directory_symlink")
                else:
                    self._visit(path)
            elif stat.S_ISREG(mode):
                self.files.append(relative)
            else:
                self.skip(relative, "special_file")

    def collect(self):
        self._visit(self.root)
        self.files.sort()
        return self

    def summary(self):
        return {
            "complete": not (self.truncated or self.skipped),
            "files_seen": len(self.files),
            "truncated": self.truncated,
            "limits": {"entries": MAX_FILES, "file_bytes": MAX_BYTES},
            "skipped": self.skipped,
        }
