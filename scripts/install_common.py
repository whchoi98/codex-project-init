"""Filesystem checks shared by the plugin and standalone skill installers."""

import os
from pathlib import Path
import stat


class InstallError(ValueError):
    """An actionable installer error that contains no child-process output."""


def _absolute(path):
    path = Path(path).expanduser()
    if ".." in path.parts:
        raise InstallError("Installation paths must not contain parent traversal.")
    return path.absolute()


def _safe_path(path, *, directory, required=False):
    """Check every component without resolving away symlinks."""
    for component in reversed((path,) + tuple(path.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if component == path and required:
                raise InstallError("A required installation path is missing.") from None
            continue
        if stat.S_ISLNK(info.st_mode):
            raise InstallError("Installation paths and ancestors must not be symlinks.")
        want_directory = component != path or directory
        if want_directory and not stat.S_ISDIR(info.st_mode):
            raise InstallError("An installation directory or ancestor is not a directory.")
        if not want_directory and not stat.S_ISREG(info.st_mode):
            raise InstallError("An installation file is not a regular file.")
        if not want_directory and info.st_nlink != 1:
            raise InstallError("Installation files must not have multiple hard links.")


def _writable_parent(path):
    while not path.exists():
        path = path.parent
    if not os.access(path, os.W_OK | os.X_OK):
        raise InstallError("An installation parent directory is not writable.")


def _identity(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    return info.st_dev, info.st_ino


def _overlap(first, second):
    return first == second or first in second.parents or second in first.parents
