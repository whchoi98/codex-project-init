# Check and evidence review

Use this for a read-only `check` or the final review of authored documentation.
The CLI supplies structural evidence. Codex supplies the comparison between
documentation, code, and the user's request.

## Select the scope

- Broad initialization: `project_audit.py check PATH` checks core document roles.
  Conventional equivalents, such as `ARCHITECTURE.md` or `docs/index.md`, count.
- Targeted maintenance or a custom layout: use `check PATH --profile existing`.
  Add repeated `--require-document PATH` arguments for the documents the task
  actually requires. Each required path is relative to the target.
- Commit preparation: add `--for-commit`. The index, whitespace checks, dirty
  state, and reported staged paths are scoped to the target. `git.root` records
  the enclosing repository, while `git.scope` and staged paths identify the
  requested subproject.

In `check` mode, inspect and report only. Do not run project tests or scripts:
even a test command can create files or use external services. If the user also
requests fixes, perform the authorized fixes as a separate authoring operation.

## Read the limitations before the verdict

`inspect` returns observations and never claims checks passed. `check` exits 1
for errors, 0 for pass/warnings; invalid invocation exits 2. Zero is not proof of
complete coverage. Read `scan.complete`, `scan.skipped`, and findings.

The inventory omits common generated/dependency directories and, in valid Git
worktrees, honors Git ignore rules while retaining tracked files. Symlinked
directories are not traversed. External file symlinks and special files are not
read. Large files, unreadable paths, and inventory limits are reported.

Git metadata is also checked before Git runs. Metadata symlinks, local config
includes, unsupported filter overrides, or metadata limits can make Git
observations unavailable. Report that boundary; do not treat it as a clean index
or silently edit the project's Git configuration. Normal worktree pointer files
are supported.

Local Markdown/HTML file targets are checked; web availability, heading anchors,
site-generator routes, and semantic correctness are not. Template destinations
containing `{{...}}` are authoring aids, not finished project links. Check that
generated project documents no longer contain them.

Manifest commands distinguish declarations from conventional suggestions.
Single-line Python/Rust TOML metadata is a limited observation; dynamic versions,
workspace inheritance, and complex TOML need direct inspection.

Staged secret indicators recognize a limited set of text patterns and filenames.
Matching values are never shown. Skipped binary/large blobs and submodules remain
unverified; use the project's established scanner when a broader scan is required.

## Review what the helper cannot decide

Review only dimensions relevant to the request:

| Dimension | Evidence to inspect |
|---|---|
| Purpose and usage | Real entrypoints, exported behavior, and runnable examples |
| Setup and commands | Manifests, actual scripts, prerequisites, config names/defaults |
| Architecture | Real component connections and ownership, not directory names alone |
| Codex instructions | Applicable AGENTS.md, actual validation commands, non-obvious invariants |
| Maintenance | Affected docs/indexes, preserved Unreleased/history, equivalent bilingual facts |

For README/changelog authoring, also review their
[README](readme.md) and [CHANGELOG](changelog.md) contracts under the selected
structure. Compare section order, applicable sections, executable examples,
configuration values, and version/category entries across languages. Check badge
evidence and link definitions; preserve custom content and released blocks.
These are semantic reviews, not checks the helper claims to automate. A custom
layout is not an error merely because it differs from a new-file template.

For each issue, name the document/location, the conflicting or missing source
evidence, and a concrete correction. Separate a confirmed mismatch from an
unverified assumption. Avoid a numerical quality score based on file presence,
word count, or an unexecuted command.

For authored changes, check that user-owned sections and historical entries were
preserved and that only the requested scope changed. If a second pass finds no
new evidence, leave the files alone.

## Handoff

Lead with the requested outcome. For findings, a compact table of severity,
location, evidence, and correction is sufficient. State which commands actually
ran and which checks remain incomplete. Missing Git metadata blocks commit
preflight; a missing remote does not block a local commit.
