# Initialize and synchronize

## Inspect

Start with the helper's `inspect` report, root instructions, manifests, existing
README/changelog, and relevant source files. Treat detected layers as candidates
to verify. In a monorepo, honor the requested package path and record the enclosing
Git root separately.

For an empty project, establish purpose and stack from the conversation. If
neither exists, ask one focused question before writing project-specific claims.

## Prepare the core

Read [document conventions](documents.md) for new public documents. Map the roles
below to the project's existing layout before creating files; an equivalent
document can satisfy a role without being renamed. Treat this as a menu of useful
project guidance, not a requirement to generate every directory.
When README or CHANGELOG is in scope, read its [README](readme.md) or
[CHANGELOG](changelog.md) guide before authoring it. Use `assets/readme.md` and
`assets/changelog.md` for missing files or an explicitly requested format adoption.
Apply the shared Shields language navigation to every new bilingual public
document, including documentation indexes and supporting guides.

- **AGENTS.md:** purpose, entrypoints, actual development/validation commands,
  non-obvious invariants, and when to update docs/changelog. Keep it concise.
- **README.md:** evidenced badges and bilingual descriptions, then the ordered
  sections in the README guide, including applicable configuration/tests/API
  details and truthful license/contact information.
- **CHANGELOG.md:** Keep a Changelog notices, Unreleased, supplied release
  history, standard English category names, and evidenced version links.
- **docs/README.md:** links to real architecture, onboarding, reference, ADR,
  and operational documents.
- **docs/architecture.md:** real components, data flow, design constraints,
  Mermaid diagram, and code pointers.
- **docs/onboarding.md:** prerequisites, install/start/check commands, and the
  project's actual local workflow.
- **CONTRIBUTING.md:** how to review changes, run checks, prepare a commit,
  and use the established branch/PR process.
- **.gitignore / .editorconfig:** fill genuine gaps using the existing stack.
  Preserve intentional rules and tracked examples.

Use `docs/README.md`, `docs/decisions/`, `docs/runbooks/`, and
`docs/reference/INDEX.md` when no equivalent organization exists. Create indexes
when there is real content to link, and keep AGENTS.md focused on instructions.

Use `assets/` as authoring guidance. Fill every variable with evidence or clearly
state an unknown fact. Do not leave template tokens as finished documentation.
Do not choose or change a license for the user.

## Add only relevant supporting material

Create reference documents for detected, verified layers; custom names such as
`terminal`, `session-data`, or `plugin-installation` are allowed. Document
operations that actually exist, such as local development, packaging, releases,
or deployment. Create ADRs from known decisions, with inferred rationale clearly
identified for review.

Do not generate generic skills, agents, hooks, MCP servers, cloud resources,
source folders, or test suites merely to match a diagram.

## Synchronize an existing repository

`sync`, `sync-doc`, and `sync-docs` select this same workflow.

Inspect changed files and current documents. Update affected descriptions,
commands, links, versions, diagrams, and indexes; keep custom content and
historical records. Reconcile both languages when a doc is already bilingual.
Do not claim freshness only from modification time or a file-count score.
Keep the shared language badge row consistent across affected bilingual
documents, preserving existing headings and legacy anchor destinations.

1. Identify the relevant source change and map it to existing document sections.
   Read the README/changelog guides for affected files and select the structure
   using the conventions. A sync is not an implicit format or language migration.
2. Update README sections in place. Keep the canonical order in documents that
   use it, preserve custom notes, and reconcile both languages' commands,
   configuration tables, tree paths, links, and evidenced badges. Add/remove a
   conditional section only when its applicability actually changes.
3. Add or correct user-visible changes under each language's Unreleased.
   Match entries by their meaning so translation changes do not duplicate them.
   Preserve released blocks, dates, versions, category names, and link targets.
   Moving entries into a release requires a release request.
4. Review the diff for lost custom content, language drift, duplicate sections,
   and historical changes. With no new source evidence, a repeated sync leaves
   document bytes unchanged.

Preserve managed-region boundaries when present. If a legacy layout already
expresses the relevant information accurately, leave its headings alone.

Add scoped AGENTS.md only when different instructions are needed for that
directory. Do not create one in every utility or asset directory.

Check published artifacts too: if the README links to packaged documentation,
ensure the package includes it or clearly points to an established external URL.
Regenerate repository-owned archives after the final source/document edit.

## Verify

Run `project_audit.py check PATH` after broad initialization. For a targeted
sync/custom layout, use `--profile existing` with `--require-document` for
requested deliverables. Review [semantic evidence](check.md) and run relevant
project checks for authored changes. Preserve successful historical test reports
as historical evidence; record fresh executions separately.

Report changed files, performed checks, and concrete gaps. Distinguish missing
Git metadata/remotes from documentation errors.
