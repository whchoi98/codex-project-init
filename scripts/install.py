#!/usr/bin/env python3
"""Install a Codex plugin (default) or a standalone project-init skill."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Dict, Optional, Tuple


# Importing the shared validator must not create files during a dry run.
sys.dont_write_bytecode = True
if __package__:
    from .install_common import (
        InstallError, _absolute, _identity, _overlap, _safe_path, _writable_parent,
    )
else:
    from install_common import (
        InstallError, _absolute, _identity, _overlap, _safe_path, _writable_parent,
    )

SOURCE = Path(__file__).absolute().parents[1]
NAME = "codex-project-init"
HELPER_OPTIONS = {
    "create_basic_plugin.py": ("--path", "--with-marketplace", "--marketplace-path"),
    "read_marketplace_name.py": ("--marketplace-path",),
    "update_plugin_cachebuster.py": ("plugin_path",),
}


@dataclass(frozen=True)
class InstallPlan:
    source: Path
    destination: Path
    marketplace: Path
    helpers: Path
    codex: str
    marketplace_name: str
    add_marketplace_entry: bool
    replace_existing_source: bool
    files: Tuple[Path, ...] = field(repr=False)
    environment: Dict[str, str] = field(repr=False)
    marketplace_bytes: Optional[bytes] = field(repr=False)
    destination_identity: Optional[Tuple[int, int]] = field(repr=False)

    def report(self):
        return {
            "source": str(self.source),
            "destination": str(self.destination),
            "marketplace": str(self.marketplace),
            "marketplace_name": self.marketplace_name,
            "add_marketplace_entry": self.add_marketplace_entry,
            "replace_existing_source": self.replace_existing_source,
            "install_command": self.install_command(),
        }

    def install_command(self):
        return [self.codex, "plugin", "add", NAME + "@" + self.marketplace_name]


@dataclass
class InstallState:
    backup: Optional[Path] = None
    source_published: bool = False
    marketplace_published: bool = False
    cli_attempted: bool = False
    retain_work: bool = False


def _command(command, label, environment, *, cwd=None, timeout=30):
    """Keep all child output private, including exception strings and tracebacks."""
    try:
        result = subprocess.run(
            command, env=environment, cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise InstallError(label + " timed out; command output withheld.") from None
    except OSError:
        raise InstallError(label + " could not start; command output withheld.") from None
    if result.returncode:
        raise InstallError(
            "{} failed (exit {}); command output withheld.".format(label, result.returncode)
        )
    return result.stdout.decode("utf-8", errors="replace")


def _helper(helpers, name, args, environment):
    return _command(
        [sys.executable, "-I", "-B", str(helpers / name)] + list(args),
        "Codex helper " + name, environment,
    )


def _source_payload(source):
    # Both direct script execution and `from scripts import install` are useful.
    try:
        if __package__:
            from .distribution import DistributionError, payload_files, validate_source
        else:
            from distribution import DistributionError, payload_files, validate_source
    except ImportError:
        raise InstallError(
            "Shared distribution support is missing; use a complete plugin checkout or archive."
        ) from None
    try:
        manifest = validate_source(source)
        files = tuple(payload_files(source))
    except (DistributionError, OSError, ValueError):
        raise InstallError("Source validation failed; check the manifest and safe payload files.") from None
    if manifest.get("name") != NAME:
        raise InstallError("Source is not the expected Codex Project Init plugin.")
    for path in files:
        if not path.is_absolute() or source not in path.parents:
            raise InstallError("The distribution payload must stay inside its source.")
        _safe_path(path, directory=False, required=True)
    return manifest, files


def _read_marketplace(path, helpers, environment):
    _safe_path(path, directory=False)
    if not path.exists():
        return None, "personal", False
    contents = path.read_bytes()
    name = _helper(
        helpers, "read_marketplace_name.py", ["--marketplace-path", str(path)], environment,
    ).strip()
    if re.fullmatch(r"[A-Za-z0-9_-]+", name) is None:
        raise InstallError("The marketplace helper did not return a valid identifier.")

    def unique_fields(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError

    try:
        payload = json.loads(
            contents, object_pairs_hook=unique_fields, parse_constant=reject_constant,
        )
    except (ValueError, UnicodeError):
        raise InstallError(
            "The existing marketplace must contain strict JSON without duplicate keys."
        ) from None
    if not isinstance(payload, dict) or payload.get("name") != name:
        raise InstallError("The existing marketplace must be an object with a valid name.")
    interface = payload.get("interface")
    if interface is not None and not isinstance(interface, dict):
        raise InstallError("The existing marketplace interface must be an object.")
    entries = payload.get("plugins", [])
    if not isinstance(entries, list):
        raise InstallError("The existing marketplace plugins must be an array.")
    seen = set()
    existing = False
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise InstallError("Each marketplace entry must be an object with a name.")
        entry_name = entry["name"]
        if re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*", entry_name) is None:
            raise InstallError("A marketplace entry has an invalid plugin identifier.")
        if entry_name in seen:
            raise InstallError("The marketplace contains duplicate plugin entries.")
        seen.add(entry_name)
        if entry_name == NAME:
            if entry.get("source") != {"source": "local", "path": "./plugins/" + NAME}:
                raise InstallError("The existing marketplace entry points to a different source.")
            existing = True
    return contents, name, existing


def build_plan(*, source=SOURCE, home=None, codex_home=None, helpers=None,
               codex=None, replace=False, environment=None):
    """Run all read-only preflight without creating the home or destination."""
    environment = dict(os.environ if environment is None else environment)
    home = _absolute(home if home is not None else environment.get("HOME", Path.home()))
    codex_home = _absolute(
        codex_home if codex_home is not None
        else environment.get("CODEX_HOME", home / ".codex")
    )
    source = _absolute(source)
    destination = home / "plugins" / NAME
    marketplace = home / ".agents/plugins/marketplace.json"
    helpers = _absolute(
        helpers if helpers is not None else codex_home / "skills/.system/plugin-creator/scripts"
    )
    if home == Path(home.anchor) or codex_home == Path(codex_home.anchor):
        raise InstallError("The filesystem root is not a safe installation home.")
    if _overlap(source, destination) or _overlap(source, marketplace):
        raise InstallError("The source must be separate from the installation destination.")
    if _overlap(destination, codex_home) or _overlap(destination, helpers):
        raise InstallError("The destination must be separate from Codex state and helpers.")
    _safe_path(source, directory=True, required=True)
    _safe_path(home, directory=True)
    _safe_path(codex_home, directory=True)
    _safe_path(destination, directory=True)
    _safe_path(marketplace, directory=False)
    _, files = _source_payload(source)
    environment["HOME"] = str(home)
    environment["CODEX_HOME"] = str(codex_home)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, required_options in HELPER_OPTIONS.items():
        _safe_path(helpers / name, directory=False, required=True)
        usage = _helper(helpers, name, ["--help"], environment)
        if any(option not in usage for option in required_options):
            raise InstallError("Codex plugin-creator helpers do not support the required options.")
    executable = shutil.which(str(codex or "codex"), path=environment.get("PATH", os.defpath))
    if executable is None:
        raise InstallError("A working Codex executable is required; select one with --codex.")
    executable = str(Path(executable).absolute())
    usage = _command(
        [executable, "plugin", "add", "--help"],
        "Codex plugin add capability check", environment, cwd=source,
    )
    if re.search(r"(?m)^Usage:[ \t]+\S+[ \t]+plugin[ \t]+add(?:[ \t]|$)", usage) is None:
        raise InstallError(
            "The selected Codex executable does not advertise plugin add support; "
            "select a compatible CLI with --codex."
        )
    contents, marketplace_name, existing = _read_marketplace(marketplace, helpers, environment)
    identity = _identity(destination)
    if identity is not None and not replace:
        raise InstallError("Destination exists. Review it and use --replace for a backed-up update.")
    _writable_parent(destination.parent)
    if not existing:
        _writable_parent(marketplace.parent)
    return InstallPlan(
        source, destination, marketplace, helpers, executable, marketplace_name,
        not existing, identity is not None, files, environment, contents, identity,
    )


def _unchanged(plan):
    _safe_path(plan.source, directory=True, required=True)
    _safe_path(plan.destination, directory=True)
    _safe_path(plan.marketplace, directory=False)
    if _identity(plan.destination) != plan.destination_identity:
        raise InstallError("The destination changed after preflight; run the installer again.")
    current = plan.marketplace.read_bytes() if plan.marketplace.exists() else None
    if current != plan.marketplace_bytes:
        raise InstallError("The marketplace changed after preflight; run the installer again.")


def prepare_candidate(plan, work):
    """Copy only the shared payload into an empty directory, then cachebust it."""
    candidate = work / NAME
    candidate.mkdir()
    for source_file in plan.files:
        _safe_path(source_file, directory=False, required=True)
        destination_file = candidate / source_file.relative_to(plan.source)
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file, follow_symlinks=False)
    _helper(
        plan.helpers, "update_plugin_cachebuster.py", [str(candidate)], plan.environment,
    )
    manifest, _ = _source_payload(candidate)
    return candidate, manifest["version"]


def prepare_marketplace(plan, work):
    """Let Codex modify a private copy; never edit marketplace JSON ourselves."""
    if not plan.add_marketplace_entry:
        return None
    staged = work / "marketplace.json"
    if plan.marketplace_bytes is not None:
        staged.write_bytes(plan.marketplace_bytes)
    _helper(
        plan.helpers, "create_basic_plugin.py",
        [NAME, "--path", str(work / "scaffold"), "--with-marketplace",
         "--marketplace-path", str(staged)],
        plan.environment,
    )
    _, name, existing = _read_marketplace(staged, plan.helpers, plan.environment)
    if name != plan.marketplace_name or not existing:
        raise InstallError("The generated marketplace does not match the installation plan.")
    return staged


def publish_marketplace(plan, staged):
    """Atomically publish helper-generated bytes, even across filesystems."""
    _safe_path(plan.marketplace, directory=False)
    plan.marketplace.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".marketplace-", dir=plan.marketplace.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(handle, "wb") as output, staged.open("rb") as source:
            shutil.copyfileobj(source, output)
        if plan.marketplace.exists():
            temporary.chmod(stat.S_IMODE(plan.marketplace.stat().st_mode))
        current = plan.marketplace.read_bytes() if plan.marketplace.exists() else None
        if current != plan.marketplace_bytes:
            raise InstallError("The marketplace changed after preflight; run the installer again.")
        os.replace(temporary, plan.marketplace)
    finally:
        if temporary.exists():
            temporary.unlink()


def rollback(plan, state, work):
    """Restore source bytes; describe unsupported marketplace/cache rollback."""
    messages = []
    if state.backup is not None and os.path.lexists(state.backup):
        try:
            _safe_path(plan.destination.parent, directory=True, required=True)
            _safe_path(work, directory=True, required=True)
            _safe_path(state.backup, directory=True, required=True)
            if os.path.lexists(plan.destination):
                os.replace(plan.destination, work / "failed-source")
            os.replace(state.backup, plan.destination)
            messages.append("Previous source restored.")
        except (OSError, InstallError):
            state.retain_work = True
            messages.append("Source recovery needs review; the backup is at " + str(state.backup) + ".")
        else:
            try:
                state.backup.parent.rmdir()
            except OSError:
                messages.append("Backup container retained at " + str(state.backup.parent) + ".")
    elif state.source_published:
        try:
            _safe_path(plan.destination.parent, directory=True, required=True)
            _safe_path(work, directory=True, required=True)
            if state.marketplace_published or not plan.add_marketplace_entry:
                candidate = work / NAME
                _safe_path(candidate, directory=True, required=True)
                _source_payload(candidate)
                if os.path.lexists(plan.destination):
                    os.replace(plan.destination, work / "failed-source")
                os.replace(candidate, plan.destination)
                messages.append(
                    "Complete source retained at " + str(plan.destination)
                    + "; review Codex state and retry with --replace."
                )
            else:
                os.replace(plan.destination, work / "failed-source")
                messages.append("Unpublished source removed.")
        except (OSError, InstallError):
            state.retain_work = True
            messages.append("Source recovery needs review at " + str(plan.destination) + ".")
    if state.marketplace_published:
        messages.append(
            "The helper-generated marketplace entry remains; no supported helper removes it."
        )
    if state.cli_attempted:
        messages.append(
            "Codex marketplace/cache state may have changed and was not rolled back."
        )
    return " ".join(messages)


def install(plan):
    """Prepare a candidate before moving source, retaining a backup on success."""
    _unchanged(plan)
    plan.destination.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="." + NAME + "-install-", dir=plan.destination.parent))
    state = InstallState()
    error = None
    result = None
    try:
        candidate, version = prepare_candidate(plan, work)
        staged_marketplace = prepare_marketplace(plan, work)
        # Retain a complete recovery copy until external CLI effects finish.
        ready = work / "ready" / NAME
        shutil.copytree(candidate, ready)
        _unchanged(plan)
        if plan.replace_existing_source:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-")
            backup_parent = Path(tempfile.mkdtemp(
                prefix="." + NAME + "-backup-" + timestamp, dir=plan.destination.parent,
            ))
            state.backup = backup_parent / NAME
            os.replace(plan.destination, state.backup)
        os.replace(ready, plan.destination)
        state.source_published = True
        if staged_marketplace is not None:
            publish_marketplace(plan, staged_marketplace)
            state.marketplace_published = True
        state.cli_attempted = True
        _command(
            plan.install_command(), "Codex plugin installation", plan.environment,
            cwd=plan.destination.parent, timeout=120,
        )
        result = {
            **plan.report(), "installed_version": version,
            "backup": str(state.backup) if state.backup is not None else None,
        }
    except (Exception, KeyboardInterrupt) as failure:
        message = str(failure) if isinstance(failure, InstallError) else "Installation could not finish."
        recovery = rollback(plan, state, work)
        error = InstallError((message + " " + recovery).strip())
    if state.retain_work:
        error = InstallError(str(error) + " Recovery files retained at " + str(work) + ".")
    else:
        try:
            _safe_path(work, directory=True, required=True)
            shutil.rmtree(work)
        except (OSError, InstallError):
            message = "Temporary installation files remain at " + str(work) + "."
            if error is not None:
                error = InstallError(str(error) + " " + message)
            else:
                result["cleanup_warning"] = message
    if error is not None:
        raise error from None
    return result


def main(argv=None, *, source=SOURCE, home=None, codex_home=None, helpers=None, environment=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plugin", "skill"), default="plugin",
                        help="Install a plugin (default) or a standalone skill.")
    parser.add_argument("--project", metavar="PATH",
                        help="Install into an existing project's .agents/skills (skill mode only).")
    parser.add_argument("--dry-run", action="store_true", help="Run read-only preflight and show the plan.")
    parser.add_argument("--codex", help="Use a specific Codex executable when multiple installations exist.")
    parser.add_argument("--replace", action="store_true",
                        help="Back up and replace an existing source installation.")
    args = parser.parse_args(argv)
    if args.mode == "skill" and args.codex is not None:
        parser.error("--codex is valid only in plugin mode.")
    if args.mode != "skill" and args.project is not None:
        parser.error("--project is valid only in skill mode.")
    try:
        if args.mode == "skill":
            if __package__:
                from . import skill_install
            else:
                import skill_install
            plan = skill_install.build_plan(
                source=source, home=home, project=args.project,
                replace=args.replace, environment=environment,
            )
            result = plan.report() if args.dry_run else skill_install.install(plan)
        else:
            plan = build_plan(
                source=source, home=home, codex_home=codex_home, helpers=helpers,
                codex=args.codex, replace=args.replace, environment=environment,
            )
            result = plan.report() if args.dry_run else install(plan)
    except (InstallError, OSError, ValueError) as error:
        message = str(error) if isinstance(error, InstallError) else "Installation preflight or filesystem access failed."
        print("Installation failed: " + message, file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
