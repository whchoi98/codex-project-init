# Document conventions

Use these conventions for new public documents. A user's instructions and the
target's existing conventions take priority.

## Language and style

The source project uses English first, then Korean, with explicit ASCII anchors:

```html
<a href="#english">English</a> · <a href="#korean">한국어</a>
<a id="english"></a>
<a id="korean"></a>
```

Place the anchors immediately before their respective language headings. Keep
the same facts, commands, diagrams, and section order in both parts. Translate
explanatory prose, not file paths or command syntax. Write concise, specific
English and polite Korean. Avoid decorative emoji and invented passing badges.
Use language-tagged code fences and links relative to the document.

For existing single-language docs, preserve their layout. Bilingual conversion
is a separate explicit request; do not hide an existing release history in a
rewritten template or silently translate historical entries.

## README

Explain purpose and current behavior first. Include the applicable parts of:

1. Overview and concrete features.
2. Prerequisites, installation, and a working usage example.
3. Architecture: a short Mermaid critical-path diagram and a link to the full doc.
4. Actual configuration variables, defaults, and CLI options.
5. Source/document structure and real validation commands.
6. Contribution workflow and the actual license.

Use version/license information from authoritative project files. Add repository,
CI, contact, or demo links only when established. Do not require a contact section
whose contents would have to be guessed.

## CHANGELOG

Keep Unreleased and use dated version entries, newest first. Group related work
into user-facing changes instead of copying a Git log. New documents may use
Added, Changed, Deprecated, Removed, Fixed, and Security; keep an existing
project's headings and style.

For a requested release, move only its Unreleased entries under the version/date.
Preserve older entries and corresponding evidence. Follow the existing tag
prefix and version authority. Generate comparison links only for a known remote
and actual/planned tags; omit imaginary links in a repository without a remote.

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
