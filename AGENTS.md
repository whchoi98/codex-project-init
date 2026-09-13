# Codex Project Init

This repository packages one Codex skill and a read-only repository auditor.

- Skill entrypoint: `skills/project-init/SKILL.md`.
- Runtime helper: `skills/project-init/scripts/project_audit.py`.
- Auditor implementation: sibling `scripts/project_init_audit/` package.
- Shared installation/distribution payload: `scripts/distribution.py`.
- Plugin version source: `.codex-plugin/plugin.json`.
- Preserve user content and historical changelog entries in consuming projects.
- Use the dedicated README/CHANGELOG guides and templates for new documents;
  synchronize existing sections and both languages without rewriting history.
- Keep project preparation separate from committing, pushing, and installing hooks.
  Existing user authorization still applies.
- Use Python's standard library; support Python 3.9 and later.
- The auditor must not execute project scripts, modify the target, print secret
  values, or follow file links outside the target directory.
- Preserve CLI exit codes and existing JSON fields; report skipped content and
  command provenance. Scope Git observations to the requested project path.
- Test with temporary projects and real local Git repositories. Do not push or
  use real credentials in tests.
- Run `make test`, `make check`, and `make package` for a release.
- Keep new public docs in English/Korean. Avoid fixed test/file counts in guidance.
- Rebuild distribution archives after the final source or documentation edit.
- Update `CHANGELOG.md` with user-visible changes; retain Unreleased.
- For workflow changes, use the isolated trials described in
  `docs/reference/skill-evaluation.md` in addition to helper tests.
