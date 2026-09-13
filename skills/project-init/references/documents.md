# Document conventions

Use these conventions when authoring or synchronizing public documents. Apply
the user's requested format first, then explicit target instructions, then the
existing document's structure, then the defaults below.

## Language and style

New public documents use English first, then Korean. Use one Shields language
badge row below the title throughout bilingual public documentation: README,
CHANGELOG, CONTRIBUTING, documentation indexes, architecture, onboarding, ADRs,
runbooks, and implementation references. README adds its evidenced project
badges on the same row; other documents need only the language badges.

```markdown
[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)
```

Keep the document's heading levels. `English` and `한국어` headings provide the
default destinations above. Preserve existing legacy anchors such as `#korean`
for incoming links; for custom language headings, link to their actual anchors.
When aligning an existing document with this convention, replace its plain-text
language navigation without rewriting its body. During sync, maintain one row
and verify its targets rather than appending another row.

Do not add navigation to a translation that is absent. If badge alignment is
requested for an existing single-language document, use a non-linked language
badge and preserve its language, layout, and historical content.

Keep the same facts, commands, diagrams, table data, and section order in both
languages. Translate prose and explanatory comments; keep executable tokens,
outputs, paths, variable names, and defaults identical. Directory-tree comments
may be localized while paths and indentation stay the same. Use language-tagged
fences, relative local links, and blank lines around headings/lists. Use no emoji.
README Korean uses polite sentences; changelog Korean uses concise noun endings.
English procedures and new changelog entries start with action verbs.

For existing single-language docs, preserve their layout. Bilingual conversion
is a separate explicit request; do not hide an existing release history in a
rewritten template or silently translate historical entries.

## Select and preserve the structure

| Target state | Authoring and sync behavior |
|---|---|
| Missing README or changelog | Read its dedicated guide and adapt its bilingual template |
| Existing document using the default structure | Update matching sections in place; keep heading order and language parity |
| Explicit request to adopt this format | Map existing content into the template; preserve custom sections and historical facts |
| Existing custom or single-language document | Map the guide's content roles to its existing sections; preserve layout and language |

For a broad initialization, fill applicable gaps without replacing complete
existing documents. For targeted work, change only the requested document or
sections. Retain user-owned notes, managed-region boundaries, and custom anchors.
Update incoming local links if an explicitly requested restructure changes anchors.
Never copy an example project's identity, status, version, or commands into the
target. Resolve template variables, remove inapplicable optional sections, and
remove template-only comments after applying their conditions.

## README and CHANGELOG

- Read [README authoring and sync](readme.md) for its header, ordered sections,
  conditional content, and evidence rules; adapt `assets/readme.md`.
- Read [CHANGELOG authoring and sync](changelog.md) for Keep a Changelog,
  release handling, shared version links, and historical preservation;
  adapt `assets/changelog.md`.

Treat these guides as authoring contracts, not universal auditor requirements.
The read-only CLI still supports custom layouts and does not enforce translated
semantics, badges, heading anchors, or release history.

## Architecture and implementation references

Read entrypoints and their dependencies. Use `flowchart TB` with relevant
subgraphs for a component view and `flowchart LR` for a critical path. Keep
diagram labels identical between language sections. Do not convert a local CLI
into an invented cloud architecture.

An implementation reference has Overview, Components, Key Decisions, Code
Pointers, and Cross-references. Point to real files and explain important
behavior or constraints. Paths are evidence; directory names alone do not prove
a component's responsibility.

Keep `docs/README.md` and any reference index navigable. A module guide belongs
in docs; scoped `AGENTS.md` is for instructions that affect work in that scope.
