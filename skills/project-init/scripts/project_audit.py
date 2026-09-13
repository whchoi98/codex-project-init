#!/usr/bin/env python3
"""Read-only project observations and documentation/Git preflight checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Running the auditor from inside its own target must not create __pycache__.
sys.dont_write_bytecode = True

from project_init_audit.documents import CORE_DOCUMENTS, document_findings, is_document
from project_init_audit.filesystem import Inventory, finding
from project_init_audit.git import MAX_METADATA_ENTRIES, Repository
from project_init_audit.project import project_info


def audit(root, mode, for_commit=False, profile="core", required=()):
    repository = Repository(root)
    inventory = Inventory(root, repository.candidates()).collect()
    git_info = repository.info()
    documents = [path for path in inventory.files if is_document(path)]
    issues = []
    project = project_info(root, inventory.files, inventory, issues)
    checks = []
    if mode == "check":
        issues.extend(document_findings(root, documents, inventory, profile, required))
        checks.extend(["documents", "local_links"])
        if not repository.valid:
            issues.append(finding("git_missing", ".", "No usable Git working-tree metadata was detected.",
                                  "error" if for_commit else "warning"))
            if for_commit:
                inventory.skip(".", "git_preflight_unavailable")
        elif for_commit:
            staged = repository.preflight()
            issues.extend(staged)
            checks.extend(["git_preflight", "staged_indicators"])
            for issue in staged:
                if issue["code"] in {"staged_scan_failed", "staged_scan_skipped"}:
                    inventory.skip(issue["path"], issue["code"])
    for reason in dict.fromkeys(repository.failures):
        inventory.skip(".", reason)
        detail = {
            "git_external_metadata": "Git metadata uses a filesystem symlink and was not followed.",
            "git_config_include_unsupported": "Local Git configuration includes are not followed.",
            "git_metadata_truncated": "Git metadata inventory exceeded its entry limit.",
            "git_filter_override_failed": "Executable Git filters could not be disabled.",
        }.get(reason, "Git observation could not be completed.")
        issues.append(finding(reason, ".", detail,
                              "error" if for_commit else "warning"))
    if inventory.truncated:
        issues.append(finding("scan_truncated", ".", "Inventory reached its entry limit.", "warning"))
    for skipped in inventory.skipped:
        name, reason = skipped["path"], skipped["reason"]
        if any(f["path"] == name for f in issues):
            continue
        mandatory = name in required or profile == "core" and any(
            option == name or option.startswith(name + "/")
            for group in CORE_DOCUMENTS for option in group
        )
        severity = ("error" if mode == "check" and (mandatory or is_document(name))
                    and reason in {"external_symlink", "unresolvable_path"} else "warning")
        issues.append(finding(reason, name, "Not read: " + reason + ".", severity))
    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    scan = inventory.summary()
    scan["limits"]["git_metadata_entries"] = MAX_METADATA_ENTRIES
    return {
        "schema_version": 1,
        "root": str(root), "mode": mode, "for_commit": for_commit,
        "profile": profile if mode == "check" else None,
        "required_documents": list(required),
        "project": project, "git": git_info,
        "documents": documents, "excluded_external_links": inventory.excluded,
        "claude_files": [p for p in inventory.files
                         if p == "CLAUDE.md" or p.startswith(".claude/")],
        "scan": scan,
        "findings": issues, "error_count": errors, "warning_count": warnings,
        "status": "observed" if mode == "inspect" else "fail" if errors else "warn" if issues else "pass",
        "checks_run": checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "check"))
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--for-commit", action="store_true",
                        help="Require valid Git metadata and inspect the scoped index.")
    parser.add_argument("--profile", choices=("core", "existing"), default=None,
                        help="Check core documentation (default) or only existing documents.")
    parser.add_argument("--require-document", action="append", default=[], metavar="PATH",
                        help="Also require this project-relative document; repeat as needed.")
    args = parser.parse_args(argv)
    if args.mode != "check" and (args.for_commit or args.profile or args.require_document):
        parser.error("--for-commit, --profile, and --require-document require check")
    for name in args.require_document:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or name in {"", "."}:
            parser.error("--require-document must be a nonempty path inside the project")
    try:
        root = Path(args.path).expanduser().resolve()
        if not root.is_dir():
            parser.error("target must be an existing directory")
    except (OSError, RuntimeError, ValueError):
        parser.error("target must be a resolvable existing directory")
    report = audit(root, args.mode, args.for_commit, args.profile or "core", args.require_document)
    # ASCII escaping also preserves undecodable filesystem paths in valid JSON.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if args.mode == "check" and report["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
