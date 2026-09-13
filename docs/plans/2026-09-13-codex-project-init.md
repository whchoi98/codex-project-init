# Codex Project Init implementation plan

**Goal:** Provide the user's project-init documentation workflow as a discoverable
Codex plugin and a portable standalone skill.

**Source:** `project-init` 2.4.0 in the adjacent Claude Code repository. The installed
Claude copy is older; use the maintained source as the functional reference.

**Architecture:** One `project-init` skill routes to focused authoring references.
A Python standard-library helper inspects a target and performs read-only checks.
Codex authors project-specific content; a template copier does not invent it.
The source repository is separate from the HUD. Installation uses the personal
marketplace and the supported Codex plugin helpers.

## Work

- [x] Author the skill, authoring templates, and workflow references.
- [x] Implement `project_audit.py inspect PATH` and `check PATH [--for-commit]`.
  Both output JSON. Inspection returns observations; check exits 1 for findings
  marked error. Invalid invocation exits 2. Neither writes to the target.
- [x] Verify real manifest detection, document links, missing Git metadata, and
  staged content independently from unstaged working-tree content.
- [x] Document the plugin itself: README, changelog, architecture, onboarding,
  contributions, and release/installation instructions.
- [x] Validate skill/plugin metadata.
- [x] Apply the workflow to my-codex-hud, preserving its released history.

## Delivery procedure

Build plugin and standalone skill ZIPs after the final edits. Register/install
through the personal marketplace while preserving existing entries. Verify the
runtime skill list without a model request, and run the HUD's required checks.
Environment-specific installation receipts and validation results belong in the
delivery report, rather than being asserted for every copy of the source package.

## Mapping

Claude commands become modes of `$project-init`; project context becomes
`AGENTS.md`. Public documentation keeps the original bilingual/Mermaid approach.
Claude-specific hooks, tool allowlists, and subagent configuration require a
separate compatibility assessment and are not silently installed as Codex config.

## Completion evidence

Tests exercise files and Git behavior, not template wording. Check generated
artifact contents/checksums, validate reference targets, and query Codex's actual
skill list. Report source and installed locations plus any pending Git setup.
