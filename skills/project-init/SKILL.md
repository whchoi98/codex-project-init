---
name: project-init
description: "Create, synchronize, or check repository documentation: AGENTS.md, README, CHANGELOG, architecture, ADRs, and runbooks. Use for project-init, 프로젝트 문서 정리, 문서 동기화, 문서 점검, or explicitly requested documentation preparation before a commit. Ordinary Git commit/push and general code review are separate workflows."
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
An ordinary commit/push request alone does not select Project Init. Continue the
authorized Git task without adding documentation synchronization or a new review
pipeline. Keep explicit `prepare-commit` available for documentation preparation.

| Request or mode | Workflow |
|---|---|
| `init`, `init-project`, broad project preparation | Fill applicable documentation gaps: [initialize](references/initialize.md) |
| `readme`, `generate-readme` | Author or update README: [README guide](references/readme.md) |
| `changelog`, `generate-changelog` | Update Unreleased or a requested release: [CHANGELOG guide](references/changelog.md) |
| `sync`, `sync-doc`, `sync-docs` | Update affected sections in their established structure: [initialize and sync](references/initialize.md) |
| `check`, `health-check` | Read-only findings: [check and review](references/check.md) |
| `prepare-commit`, 문서 커밋 준비 | Affected docs and index checks, reusing valid results: [Git preparation](references/git-preparation.md) |
| `add-module`, `add-adr`, `add-runbook`, `add-reference-doc` | One requested addition: [targeted additions](references/additions.md) |
| `migrate`, `migrate-hooks` | [Claude adaptation](references/migration.md), with runtime compatibility verified |

## Start with evidence

Default to affected-document checks. Project Init owns documentation verification;
existing development, review, and CI workflows keep ownership of implementation
tests and code review. Read [verification scope and reuse](references/verification.md)
when coordinating checks, preparing a commit, or deciding whether evidence applies.

Read applicable `AGENTS.md` instructions and inspect the target. Resolve this
skill's directory from its installed path, not the working directory:

```bash
python3 /absolute/skill/path/scripts/project_audit.py inspect /absolute/project/path
```

The helper reports manifests, command provenance, candidate implementation
layers, existing documents, scoped Git state, and scan limits. It never executes
project scripts or contacts remotes. Keep the entire installed skill directory;
the entrypoint depends on its sibling Python package.
Use `inspect` when authoring needs initial observations. For a read-only check,
run the selected `check` directly: its report already contains those observations.
Reuse a current report from the same target/state instead of rescanning it.

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
- Use the shared Shields language badges throughout bilingual public documents,
  including `docs/` pages, ADRs, runbooks, and implementation references.
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

Choose one final audit for the current target/state. Use the core profile for
broad initialization:

```bash
python3 /absolute/skill/path/scripts/project_audit.py check /absolute/project/path
```

Use `--profile existing`
for targeted work or a custom layout. Add `--require-document relative/path.md`
to require a specific document. For commit preparation add `--for-commit`; Git
checks stay within the requested path and read staged blobs from the index.
Combine the appropriate flags in that audit instead of running every variant.

Read [check and review](references/check.md) for the evidence review. Inspect
`scan.complete` and findings before claiming coverage. The helper checks file
targets and selected Git indicators; it cannot establish semantic accuracy.
In `check` mode, do not edit files, run project scripts/tests, stage, or install
anything. For authoring or commit preparation, apply the verification policy:
ordinary documentation edits do not trigger application tests; reuse valid
existing test/review evidence and execute only missing, required checks.
Do not start a second code reviewer or tester merely because this skill is active.

Preparing a repository does not itself request a commit, tag, push, remote
creation, hook installation, or deployment. If the user already authorized those
actions, proceed within that scope without asking again. Stage only intended
files, inspect the exact staged diff, and preserve unrelated staged work.

Finish with the requested result, changed paths (or read-only findings), checks
executed, evidence reused, checks not needed or still missing, and concrete gaps.
Distinguish detection, review, and
execution. Report installation/runtime limits only when they affect the task.
