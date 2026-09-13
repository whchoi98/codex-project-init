"""Install the complete standalone skill from a validated byte snapshot."""

from contextlib import ExitStack
from dataclasses import dataclass, field
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Dict, Optional, Tuple


sys.dont_write_bytecode = True
if __package__:
    from .install_common import (
        InstallError, _absolute, _identity, _overlap, _safe_path, _writable_parent,
    )
    from .distribution import DistributionError, SKILL_NAME, SKILL_ROOT, source_snapshot
else:
    from install_common import (
        InstallError, _absolute, _identity, _overlap, _safe_path, _writable_parent,
    )
    from distribution import DistributionError, SKILL_NAME, SKILL_ROOT, source_snapshot


SOURCE = Path(__file__).absolute().parents[1]


@dataclass(frozen=True)
class SkillInstallPlan:
    source: Path
    destination: Path
    project: Optional[Path]
    version: str
    files: Tuple[Tuple[Path, bytes], ...] = field(repr=False)
    destination_identity: Optional[Tuple[int, int]] = field(repr=False)
    ancestors: Tuple[Tuple[Path, Tuple[int, int]], ...] = field(repr=False)

    def report(self):
        return {
            "mode": "skill",
            "source": str(self.source),
            "destination": str(self.destination),
            "scope": "project" if self.project is not None else "user",
            "project": str(self.project) if self.project is not None else None,
            "replace_existing_source": self.destination_identity is not None,
        }


@dataclass
class Directory:
    """An open directory; path is diagnostic text, never a mutation operand."""

    path: Path
    descriptor: int
    identity: Tuple[int, int]
    stack: ExitStack = field(repr=False)
    parent: Optional["Directory"] = field(default=None, repr=False)
    entries: Dict[str, object] = field(default_factory=dict, repr=False)


@dataclass
class SkillInstallState:
    parent: Directory
    work: Directory
    candidate: Optional[Directory] = None
    backup: Optional[Directory] = None
    retain_work: bool = False


def _require_descriptor_support():
    """Fail closed; Python's path-only fallbacks cannot prevent these races."""
    missing = [
        name for name in ("O_DIRECTORY", "O_NOFOLLOW")
        if not getattr(os, name, 0)
    ]
    missing.extend(
        "os." + name + "(dir_fd)"
        for name in ("open", "mkdir", "stat", "rename", "unlink", "rmdir")
        if getattr(os, name) not in os.supports_dir_fd
    )
    if os.listdir not in os.supports_fd:
        missing.append("os.listdir(fd)")
    if os.stat not in os.supports_follow_symlinks:
        missing.append("os.stat(follow_symlinks=False)")
    if missing:
        raise InstallError(
            "Standalone skill installation requires directory-descriptor filesystem "
            "support; unavailable: " + ", ".join(missing) + "."
        )


def _stat_identity(info):
    return info.st_dev, info.st_ino


def _entry_stat(parent, name):
    try:
        return os.stat(name, dir_fd=parent.descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _directory_identity(parent, name):
    info = _entry_stat(parent, name)
    if info is None:
        return None
    if not stat.S_ISDIR(info.st_mode):
        raise InstallError("An installation directory became a symlink or special file.")
    return _stat_identity(info)


def _expect_directory(parent, name, identity):
    if _directory_identity(parent, name) != identity:
        raise InstallError("An installation directory changed; recovery needs review.")


def _open_directory(parent, name, *, expected=None):
    before = _directory_identity(parent, name)
    if before is None or (expected is not None and before != expected):
        raise InstallError("An installation directory changed; run the installer again.")
    descriptor = os.open(
        name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=parent.descriptor,
    )
    parent.stack.callback(os.close, descriptor)
    identity = _stat_identity(os.fstat(descriptor))
    if identity != before:
        raise InstallError("An installation directory changed while opening it.")
    _expect_directory(parent, name, identity)
    return Directory(parent.path / name, descriptor, identity, parent.stack, parent)


def _create_directory(parent, name, *, mode=0o755):
    os.mkdir(name, mode, dir_fd=parent.descriptor)
    try:
        directory = _open_directory(parent, name)
    except (OSError, InstallError):
        raise InstallError(
            "Created installation directory needs review at " + str(parent.path / name) + "."
        ) from None
    parent.entries[name] = directory
    return directory


def _temporary_directory(parent, prefix):
    for _attempt in range(32):
        name = prefix + secrets.token_hex(12)
        try:
            return _create_directory(parent, name, mode=0o700)
        except FileExistsError:
            continue
    raise InstallError("Could not reserve a private installation directory.")


def _open_parent(plan, stack):
    """Open every ancestor without links; mkdirat missing parents in pinned dirs."""
    expected = dict(plan.ancestors)
    anchor = Path(plan.destination.anchor)
    descriptor = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    stack.callback(os.close, descriptor)
    identity = _stat_identity(os.fstat(descriptor))
    if identity != expected.get(anchor):
        raise InstallError("The installation root changed after preflight.")
    current = Directory(anchor, descriptor, identity, stack)
    for name in plan.destination.parent.parts[1:]:
        path = current.path / name
        if _entry_stat(current, name) is None:
            if path in expected:
                raise InstallError("An installation ancestor disappeared after preflight.")
            try:
                os.mkdir(name, 0o755, dir_fd=current.descriptor)
            except FileExistsError:
                pass
        current = _open_directory(current, name, expected=expected.get(path))
    return current


def _check_chain(directory):
    chain = []
    while directory.parent is not None:
        chain.append(directory)
        directory = directory.parent
    for child in reversed(chain):
        _expect_directory(child.parent, child.path.name, child.identity)


def _move_directory(source, name, destination, target, identity):
    """Check ownership after rename, before the moved tree can enter cleanup."""
    _expect_directory(source, name, identity)
    _expect_directory(destination, target, None)
    os.rename(
        name, target, src_dir_fd=source.descriptor, dst_dir_fd=destination.descriptor,
    )
    _expect_directory(destination, target, identity)
    _check_chain(destination)


def _remove_owned_contents(directory):
    """Delete only recorded staging entries, always relative to held descriptors."""
    names = os.listdir(directory.descriptor)
    # Refuse unexpected entries before deleting anything from this directory.
    for name in names:
        owned = directory.entries.get(name)
        info = _entry_stat(directory, name)
        expected = owned.identity if isinstance(owned, Directory) else owned
        if info is None or expected is None or _stat_identity(info) != expected:
            raise InstallError("Unexpected staging content was retained for review.")
    for name in names:
        owned = directory.entries[name]
        if isinstance(owned, Directory):
            _expect_directory(directory, name, owned.identity)
            _remove_owned_contents(owned)
            _expect_directory(directory, name, owned.identity)
            os.rmdir(name, dir_fd=directory.descriptor)
        else:
            info = _entry_stat(directory, name)
            if (info is None or not stat.S_ISREG(info.st_mode)
                    or _stat_identity(info) != owned):
                raise InstallError("Unexpected staging content was retained for review.")
            os.unlink(name, dir_fd=directory.descriptor)


def _ancestors(path):
    return tuple(
        (parent, _identity(parent))
        for parent in reversed((path,) + tuple(path.parents))
        if os.path.lexists(parent)
    )


def _check_ancestors(ancestors):
    _safe_path(ancestors[-1][0], directory=True, required=True)
    if any(_identity(path) != identity for path, identity in ancestors):
        raise InstallError("An installation ancestor changed; run the installer again.")


def build_plan(*, source=SOURCE, home=None, project=None, replace=False, environment=None):
    """Validate scope and capture the payload without creating any directories."""
    _require_descriptor_support()
    environment = dict(os.environ if environment is None else environment)
    source = _absolute(source)
    _safe_path(source, directory=True, required=True)
    if project is not None:
        project = _absolute(project)
        scope_root = project
    else:
        scope_root = _absolute(
            home if home is not None else environment.get("HOME") or Path.home(),
        )
    if scope_root == Path(scope_root.anchor):
        raise InstallError("The filesystem root is not a safe installation scope.")
    _safe_path(scope_root, directory=True, required=project is not None)
    destination = scope_root / ".agents/skills" / SKILL_NAME
    _safe_path(destination, directory=True)
    if _overlap(source / SKILL_ROOT, destination):
        raise InstallError("The source skill must be separate from the installation destination.")
    identity = _identity(destination)
    if identity is not None and not replace:
        raise InstallError("Destination exists. Review it and use --replace for a backed-up update.")
    _writable_parent(destination.parent)
    ancestors = _ancestors(destination.parent)
    try:
        manifest, payload = source_snapshot(source)
    except (DistributionError, OSError, ValueError):
        raise InstallError("Source validation failed; check the manifest and safe payload files.") from None
    prefix = SKILL_ROOT + "/"
    files = tuple(
        (Path(name[len(prefix):]), contents)
        for name, contents in payload.items() if name.startswith(prefix)
    )
    plan = SkillInstallPlan(
        source, destination, project, manifest["version"], files, identity, ancestors,
    )
    _unchanged(plan)
    return plan


def _unchanged(plan):
    _check_ancestors(plan.ancestors)
    _safe_path(plan.destination, directory=True)
    if _identity(plan.destination) != plan.destination_identity:
        raise InstallError("The destination changed after preflight; run the installer again.")


def prepare_candidate(plan, work):
    """Write captured bytes only; never import, execute, or reread skill code."""
    candidate = _create_directory(work, SKILL_NAME)
    directories = {(): candidate}
    for relative, contents in plan.files:
        parts = relative.parts
        for depth in range(1, len(parts)):
            key = parts[:depth]
            if key not in directories:
                directories[key] = _create_directory(directories[key[:-1]], key[-1])
        parent = directories[parts[:-1]]
        descriptor = os.open(
            parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o644, dir_fd=parent.descriptor,
        )
        with os.fdopen(descriptor, "wb") as output:
            parent.entries[parts[-1]] = _stat_identity(os.fstat(output.fileno()))
            output.write(contents)
    return candidate


def _check_work(state, work):
    _check_chain(work)


def _check_destination(plan, state, identity):
    _check_chain(state.parent)
    _expect_directory(state.parent, plan.destination.name, identity)


def _remove_backup_container(state):
    try:
        _check_chain(state.backup)
        if os.listdir(state.backup.descriptor):
            raise InstallError("The backup container is not empty.")
        os.rmdir(state.backup.path.name, dir_fd=state.parent.descriptor)
    except (OSError, InstallError):
        return " Backup container needs review at " + str(state.backup.path) + "."
    return ""


def rollback(plan, state, work):
    """Recover only known directories; never remove an unexpected destination."""
    try:
        _check_work(state, work)
        current = _directory_identity(state.parent, plan.destination.name)
        if state.backup is not None:
            _check_chain(state.backup)
            backup_identity = _directory_identity(state.backup, SKILL_NAME)
            if backup_identity is None and current == plan.destination_identity:
                # The backup rename did not happen, so the old skill stayed put.
                return _remove_backup_container(state).strip()
            _expect_directory(state.backup, SKILL_NAME, plan.destination_identity)
            if current is not None:
                if state.candidate is None or current != state.candidate.identity:
                    raise InstallError("The destination is no longer the installer candidate.")
                _move_directory(
                    state.parent, plan.destination.name, work, "failed-skill",
                    state.candidate.identity,
                )
                work.entries["failed-skill"] = state.candidate
            _check_work(state, work)
            _move_directory(
                state.backup, SKILL_NAME, state.parent, plan.destination.name,
                plan.destination_identity,
            )
            return "Previous skill restored." + _remove_backup_container(state)
        if state.candidate is not None and current == state.candidate.identity:
            _move_directory(
                state.parent, plan.destination.name, work, "failed-skill",
                state.candidate.identity,
            )
            work.entries["failed-skill"] = state.candidate
            _expect_directory(state.parent, plan.destination.name, None)
            return "Unpublished skill removed."
        # No backup or candidate was published here. Any new destination belongs
        # to another writer and is left alone.
        return ""
    except (Exception, KeyboardInterrupt):
        state.retain_work = True
        if state.backup is not None:
            return (
                "Skill recovery needs review; original backup path: "
                + str(state.backup.path / SKILL_NAME) + "."
            )
        return "Skill recovery needs review at " + str(plan.destination) + "."


def install(plan):
    """Stage a complete skill, publish it, and keep any replaced skill as backup."""
    _unchanged(plan)
    with ExitStack() as stack:
        parent = _open_parent(plan, stack)
        work = _temporary_directory(parent, "." + SKILL_NAME + "-install-")
        state = SkillInstallState(parent, work)
        error = None
        result = None
        try:
            _check_work(state, work)
            candidate = prepare_candidate(plan, work)
            state.candidate = candidate
            _check_work(state, work)
            _check_destination(plan, state, plan.destination_identity)
            if plan.destination_identity is not None:
                # Keep the old directory's inode alive through publication.
                _open_directory(parent, plan.destination.name, expected=plan.destination_identity)
                state.backup = _temporary_directory(parent, "." + SKILL_NAME + "-backup-")
                _check_work(state, work)
                _check_destination(plan, state, plan.destination_identity)
                _move_directory(
                    parent, plan.destination.name, state.backup, SKILL_NAME,
                    plan.destination_identity,
                )
            _check_work(state, work)
            _check_destination(plan, state, None)
            _move_directory(work, SKILL_NAME, parent, plan.destination.name, candidate.identity)
            result = {
                **plan.report(), "installed_version": plan.version,
                "backup": str(state.backup.path / SKILL_NAME) if state.backup is not None else None,
            }
        except (Exception, KeyboardInterrupt) as failure:
            message = str(failure) if isinstance(failure, InstallError) else "Skill installation could not finish."
            recovery = rollback(plan, state, work)
            error = InstallError((message + " " + recovery).strip())
        if state.retain_work:
            error = InstallError(
                str(error) + " Recovery files retained in the opened installation directory; "
                "original work path: " + str(work.path) + "."
            )
        else:
            try:
                _check_work(state, work)
                _remove_owned_contents(work)
                _check_work(state, work)
                os.rmdir(work.path.name, dir_fd=parent.descriptor)
            except (OSError, InstallError):
                message = "Temporary installation directory needs review at " + str(work.path) + "."
                if error is not None:
                    error = InstallError(str(error) + " " + message)
                else:
                    result["cleanup_warning"] = message
    if error is not None:
        raise error from None
    return result
