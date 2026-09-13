# Targeted additions

Read the target's existing naming conventions and document index first. Use the
matching template in `assets/` only as a starting point.
Read [document conventions](documents.md) for language and badge formatting.
New bilingual ADRs, runbooks, and references use the same Shields language
navigation as the rest of the project's public documentation.

## add-module PATH

Honor the supplied path. Infer responsibility from existing code or the user's
description. Create application files only when requested. If new scoped
instructions are useful, write `PATH/AGENTS.md` with its role, commands,
dependencies, and special rules. Link the module from architecture/reference
docs. An empty folder is not an implemented subsystem.

## add-adr TITLE

Scan existing ADR filenames and choose the next unused numeric identifier.
Do not renumber earlier ADRs. Record status, context, considered options,
decision, consequences, and real references. Use Proposed when the decision has
not been accepted by the user. Preserve accepted historical records; supersede
them with a new ADR when appropriate.

## add-runbook NAME

Document one real operation: purpose, prerequisites, steps, verification,
failure handling/rollback, and references. Derive commands from scripts or
configuration. Distinguish a local package build from a public release or
deployment. Do not invent a rollback command for a system without one.

## add-reference-doc LAYER

Use the original layers when applicable: infrastructure, data, api, iac,
frontend, ui, security, agent-llm. Accept project-specific layer names when they
describe the actual implementation. Inspect the layer's code before writing.

Use the shared five-section structure in `assets/reference.md`. Update the
existing reference index or create `docs/reference/INDEX.md`. Preserve hand-written
content outside any explicit managed region, and avoid duplicating managed
regions when running again.

Link new documents from the project's docs index and architecture where relevant.
Use one appropriately scoped read-only audit after the addition. Apply
[verification scope and reuse](verification.md); adding a document does not
start another application-test or code-review workflow.
