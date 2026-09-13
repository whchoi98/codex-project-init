---
name: project-init
description: "Initialize and synchronize repository documentation for Codex: AGENTS.md, README, CHANGELOG, architecture, ADRs, and runbooks. Use for project-init, 프로젝트 문서 정리, 문서 동기화, or 커밋·푸시 준비. Also perform read-only documentation and staged-change checks. Does not scaffold an application."
---

# Project Init

Make an actual project understandable to its next contributor and to Codex.
Author project-specific documentation from evidence, preserve what the user
already wrote, and report what was verified.

## Select the operation

Use the requested path, otherwise the current project. Infer the operation from
the user's intent; the words below are modes, not executable slash commands.
Read only the references needed for that operation. A README request stays a
README task; missing unrelated documents do not expand it.

| Request or mode | Workflow |
|---|---|
| `init`, `init-project`, broad project preparation | Fill applicable documentation gaps: [initialize](references/initialize.md) |
| `readme`, `generate-readme` | Author or update README: [README guide](references/readme.md) |
| `changelog`, `generate-changelog` | Update Unreleased or a requested release: [CHANGELOG guide](references/changelog.md) |
| `sync`, `sync-doc`, `sync-docs` | Update affected sections in their established structure: [initialize and sync](references/initialize.md) |
| `check`, `health-check` | Read-only findings: [check and review](references/check.md) |
| `prepare-commit`, 커밋·푸시 준비 | Docs, relevant checks, and index review: [Git preparation](references/git-preparation.md) |
| `add-module`, `add-adr`, `add-runbook`, `add-reference-doc` | One requested addition: [targeted additions](references/additions.md) |
| `migrate`, `migrate-hooks` | [Claude adaptation](references/migration.md), with runtime compatibility verified |

## Start with evidence

Read applicable `AGENTS.md` instructions and inspect the target. Resolve this
skill's directory from its installed path, not the working directory:

```bash
python3 /absolute/skill/path/scripts/project_audit.py inspect /absolute/project/path
```

The helper reports manifests, command provenance, candidate implementation
layers, existing documents, scoped Git state, and scan limits. It never executes
project scripts or contacts remotes. Keep the entire installed skill directory;
the entrypoint depends on its sibling Python package.

Read the relevant entrypoints and manifests yourself before describing behavior.
Use existing source layout and commands. A conventional command is a suggestion
to verify, not a declared or successfully executed check. Do not invent API endpoints, cloud
resources, deployment commands, authors, repository URLs, test outcomes, or
release history. Missing Git metadata is a finding, not evidence of a clean repo.

For an empty project, use the purpose and stack from the conversation. Ask only
for essential information that remains unknown. Do not create application source
directories merely to populate a template.

## Preserve the existing project

- Update relevant sections while retaining user content and local conventions.
  Do not replace a README or AGENTS.md wholesale with a template.
- Preserve published changelog entries, version dates, and historical verification
  reports. Update Unreleased unless a release was requested or project rules
  specify the versioning workflow.
- Put project instructions in `AGENTS.md`. Add scoped AGENTS.md files only when a
  module has distinct commands or constraints; avoid repeating root instructions.
- New public documents default to English followed by Korean. Preserve an existing document's language/layout unless the
  user requests conversion. Code, examples, and technical claims must agree
  across language versions.
- Generate only applicable documents. A CLI does not need a fabricated REST API,
  database, frontend, security layer, or deployment platform.

- Keep equivalent document names and indexes. Fill templates in `assets/` with
  real evidence; create ADRs and runbooks only for actual decisions and operations.
- Avoid churn: a second sync with no new evidence should not rewrite prose,
  duplicate managed sections, or reorder historical records.

Read [document conventions](references/documents.md) when authoring public docs.
Initialization and synchronization also load the [README guide](references/readme.md)
and [CHANGELOG guide](references/changelog.md) for whichever of those files they
create or update. New README/changelog files use the shared bilingual templates;
existing custom layouts follow the structure-selection rules in the conventions.

## Verify the requested result

```bash
python3 /absolute/skill/path/scripts/project_audit.py check /absolute/project/path
python3 /absolute/skill/path/scripts/project_audit.py check /absolute/project/path --profile existing
```

Use the default core profile for broad initialization; use `--profile existing`
for targeted work or a custom layout. Add `--require-document relative/path.md`
to require a specific document. For commit preparation add `--for-commit`; Git
checks stay within the requested path and read staged blobs from the index.

Read [check and review](references/check.md) for the evidence review. Inspect
`scan.complete` and findings before claiming coverage. The helper checks file
targets and selected Git indicators; it cannot establish semantic accuracy.
In `check` mode, do not edit files, run project scripts/tests, stage, or install
anything. During authoring or commit preparation, run relevant project checks
within the user's scope and report their actual results.

Preparing a repository does not itself request a commit, tag, push, remote
creation, hook installation, or deployment. If the user already authorized those
actions, proceed within that scope without asking again. Stage only intended
files, inspect the exact staged diff, and preserve unrelated staged work.

Finish with the requested result, changed paths (or read-only findings), actual
verification, and concrete remaining gaps. Distinguish detection, review, and
execution. Report installation/runtime limits only when they affect the task.
