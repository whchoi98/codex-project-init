# Document conventions

Use these conventions when authoring or synchronizing public documents. Apply
the user's requested format first, then explicit target instructions, then the
existing document's structure, then the defaults below.

## Language and style

New public documents use English first, then Korean. README and CHANGELOG use
the heading anchors and Shields language badges in their dedicated guides.
Other documents may retain the project's existing ASCII navigation:

```html
<a href="#english">English</a> · <a href="#korean">한국어</a>
<a id="english"></a>
<a id="korean"></a>
```

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
