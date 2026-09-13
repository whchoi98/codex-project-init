# Claude project adaptation

This package adapts the maintained Claude `project-init` 2.4.0 workflows.
Inventory the target's actual integrations; do not assume another migrated skill
or a particular Codex runtime is installed.

| Claude capability | Codex counterpart |
|---|---|
| `/init-project` | `$project-init init` |
| `/generate-readme` | `$project-init readme` |
| `/generate-changelog` | `$project-init changelog` |
| `/sync-docs` | `$project-init sync` |
| `/health-check` | `$project-init check`, evidence-based findings |
| `/add-module` | `$project-init add-module`, scoped AGENTS.md where useful |
| `/add-adr` | `$project-init add-adr` |
| `/add-runbook` | `$project-init add-runbook` |
| `/add-reference-doc` | `$project-init add-reference-doc` |
| `/migrate-hooks` | `$project-init migrate`, compatibility assessment |
| Commit preparation | `$project-init prepare-commit` |

## Migration workflow

Read the target's CLAUDE.md and relevant `.claude/` metadata. Transfer applicable
project facts and workflow constraints into AGENTS.md, preserving an existing
AGENTS.md. Keep CLAUDE.md when the project still uses Claude.

Move reusable procedures into Codex skills only when requested and useful.
Claude slash-command frontmatter, `${CLAUDE_PLUGIN_ROOT}`, tool allowlists,
`.claude/settings.json`, and Claude agent definitions are runtime-specific.
Do not claim that copying them registers a Codex integration.

For a requested hook, subagent, MCP, or permission migration, verify the installed
Codex version and current official contract before writing configuration. Inventory
what exists, produce concrete candidate changes, preserve custom behavior, and
test the supported counterpart. Do not register integrations or change global
authentication/approval settings merely because documentation is being prepared.

The core workflow intentionally uses AGENTS.md, skills, repository docs, and a
portable read-only check command. It does not require Claude hooks, additional
agents, or external MCP servers to run.
