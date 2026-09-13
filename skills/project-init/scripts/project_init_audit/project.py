"""Project facts and command provenance from bounded, declarative inputs."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex

from .filesystem import FileNotRead, finding, safe_read
from .git import public_text

MANIFESTS = (
    "package.json", ".codex-plugin/plugin.json", "pyproject.toml", "setup.cfg",
    "setup.py", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml",
    "build.gradle", "build.gradle.kts", "Gemfile", "composer.json", "Makefile",
)


def json_manifest(root, path, inventory, issues):
    try:
        value = json.loads(safe_read(root, path))
        if not isinstance(value, dict):
            raise ValueError("not an object")
        return value
    except (FileNotRead, ValueError):
        inventory.skip(path, "manifest_not_read")
        issues.append(finding("manifest_not_read", path,
                              "Manifest is unreadable, oversized, or not a JSON object.", "warning"))
        return {}


def toml_metadata(root, path, sections, inventory, issues):
    """Read only single-line name/version/description strings on Python 3.9+.

    This is intentionally not a TOML parser. Dynamic, multiline, or inherited
    values remain unknown for the authoring agent to resolve from source.
    """
    try:
        text = safe_read(root, path).decode("utf-8")
    except (FileNotRead, UnicodeError):
        inventory.skip(path, "manifest_not_read")
        issues.append(finding("manifest_not_read", path, "Could not read TOML metadata.", "warning"))
        return {}
    result, section = {}, None
    for line in text.splitlines():
        header = re.fullmatch(r"\s*\[([^\[\]]+)\]\s*(?:#.*)?", line)
        if header:
            section = header[1].strip()
            continue
        if section not in sections:
            continue
        match = re.fullmatch(
            r"""\s*(name|version|description)\s*=\s*("(?:[^"\\]|\\.)*"|'[^']*')\s*(?:#.*)?""",
            line,
        )
        if not match:
            continue
        try:
            value = json.loads(match[2]) if match[2].startswith('"') else match[2][1:-1]
        except ValueError:
            continue
        result.setdefault(match[1], value)
    return result


def project_info(root, files, inventory, issues):
    known = set(files)
    package = json_manifest(root, "package.json", inventory, issues) if "package.json" in known else {}
    plugin = (json_manifest(root, ".codex-plugin/plugin.json", inventory, issues)
              if ".codex-plugin/plugin.json" in known else {})
    python = (toml_metadata(root, "pyproject.toml", {"project", "tool.poetry"}, inventory, issues)
              if "pyproject.toml" in known else {})
    cargo = (toml_metadata(root, "Cargo.toml", {"package"}, inventory, issues)
             if "Cargo.toml" in known else {})
    metadata = package or plugin or python or cargo
    info = {
        "name": public_text(metadata.get("name")) or root.name,
        "version": public_text(metadata.get("version")),
        "description": public_text(metadata.get("description")),
        "manifests": [path for path in MANIFESTS if path in known],
        "languages": [], "commands": {}, "command_evidence": {},
        "layers": {}, "source_directories": [],
    }

    def command(name, value, path, kind="declared"):
        if name not in info["commands"]:
            info["commands"][name] = value
            info["command_evidence"][name] = {"path": path, "kind": kind}

    if package:
        info["languages"].append("Node.js")
        manager = package.get("packageManager", "")
        manager = manager.split("@", 1)[0] if isinstance(manager, str) else ""
        if manager not in {"npm", "pnpm", "yarn", "bun"}:
            manager = next((name for file, name in [
                ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                ("bun.lock", "bun"), ("bun.lockb", "bun"),
            ] if file in known), "npm")
        scripts = package.get("scripts", {})
        if isinstance(scripts, dict):
            for name, value in scripts.items():
                if (isinstance(name, str) and isinstance(value, str)
                        and not name.startswith("-") and not any(c in name for c in "\n\r\0")
                        and public_text(name) == name):
                    command(name, f"{manager} run {shlex.quote(name)}", "package.json")
    if {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"} & known or any(
        p.endswith(".py") for p in files
    ):
        info["languages"].append("Python")
    if "Makefile" in known:
        try:
            text = safe_read(root, "Makefile").decode("utf-8")
            for line in text.splitlines():
                match = re.match(r"^([A-Za-z0-9_ -]+):(?![=])", line)
                if match:
                    for target in match[1].split():
                        if target in {"test", "check", "lint", "build", "package", "format"}:
                            command(target, "make " + target, "Makefile")
        except (FileNotRead, UnicodeError):
            inventory.skip("Makefile", "manifest_not_read")
            issues.append(finding("manifest_not_read", "Makefile", "Could not inspect Make targets.", "warning"))
    for manifest, language, default in [
        ("go.mod", "Go", "go test ./..."), ("Cargo.toml", "Rust", "cargo test"),
        ("pom.xml", "Java", "mvn test"), ("build.gradle", "Java/Kotlin", "gradle test"),
        ("build.gradle.kts", "Java/Kotlin", "gradle test"),
        ("Gemfile", "Ruby", None), ("composer.json", "PHP", None),
    ]:
        if manifest in known:
            if language not in info["languages"]:
                info["languages"].append(language)
            if default:
                command("test", default, manifest, "conventional")
    info["source_directories"] = sorted({
        path.split("/", 1)[0] for path in files if "/" in path and path.split("/", 1)[0] in
        {"src", "app", "lib", "bin", "cmd", "pkg", "internal", "components", "scripts", "skills", "plugins"}
    })
    source_files = [p for p in files if not any(
        part in {"docs", "doc", "tests", "test", "assets", "examples", "references"}
        for part in Path(p).parts
    )]
    signals = {
        "infrastructure": lambda p: Path(p).name in {"Dockerfile", "compose.yaml", "docker-compose.yml"}
            or p.startswith(("k8s/", "helm/")),
        "data": lambda p: p.startswith(("migrations/", "prisma/", "db/"))
            or p.endswith((".prisma", "schema.sql")),
        "api": lambda p: bool({"api", "routes", "controllers"} & set(Path(p).parts[:-1]))
            or Path(p).name in {"openapi.yaml", "swagger.json"},
        "iac": lambda p: p.endswith(".tf") or Path(p).name in {"cdk.json", "template.yaml", "serverless.yml"},
        "cli": lambda p: p.startswith("bin/") or Path(p).name in {"cli.js", "cli.py"},
        "plugin": lambda p: p.startswith(".codex-plugin/"),
    }
    for name, predicate in signals.items():
        evidence = [p for p in source_files if predicate(p)]
        if evidence:
            info["layers"][name] = evidence[:8]
    dependencies = {}
    for key in ("dependencies", "devDependencies"):
        if isinstance(package.get(key), dict):
            dependencies.update(package[key])
    for layer, names in [
        ("frontend", {"react", "vue", "svelte", "next", "nuxt"}),
        ("terminal", {"node-pty", "@xterm/headless", "@xterm/xterm", "blessed"}),
        ("agent-llm", {"openai", "@anthropic-ai/sdk", "langchain"}),
    ]:
        matches = sorted(names & dependencies.keys())
        if matches:
            info["layers"][layer] = ["package.json: " + name for name in matches]
    return info
