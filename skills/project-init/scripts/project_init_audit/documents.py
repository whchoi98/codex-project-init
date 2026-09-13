"""Document profiles and local Markdown/HTML file targets, not semantic scoring."""

from __future__ import annotations

import html
from pathlib import Path
import re
import string
from urllib.parse import unquote, urlsplit

from .filesystem import FileNotRead, finding, local_path, safe_read
from .git import public_text

CORE_DOCUMENTS = (
    ("AGENTS.md",),
    ("README.md", "readme.md", "README.rst", "README"),
    ("CHANGELOG.md", "CHANGES.md", "HISTORY.md", "CHANGELOG.rst"),
    (".gitignore",),
    ("docs/README.md", "docs/index.md", "doc/README.md", "doc/index.md"),
    ("docs/architecture.md", "ARCHITECTURE.md", "docs/ARCHITECTURE.md", "doc/architecture.md"),
    ("docs/onboarding.md", "docs/getting-started.md", "doc/onboarding.md"),
)
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def is_document(path):
    return Path(path).suffix.lower() in MARKDOWN_SUFFIXES


def prose(text):
    """Ignore examples and comments while retaining real prose link syntax."""
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.S)
    lines, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            token, tail = match.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
            lines.append("")
        else:
            lines.append("" if fence or line.startswith(("    ", "\t")) else line)
    text = "\n".join(lines)
    return re.sub(r"(?<!`)(`+)(?!`)(.*?)\1(?!`)", "", text, flags=re.S)


def _escaped(text, position):
    backslashes = 0
    while position > 0 and text[position - 1] == "\\":
        backslashes += 1
        position -= 1
    return backslashes % 2 == 1


def link_targets(text):
    """Extract inline/reference/HTML destinations without executing a renderer."""
    text = prose(text)
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        if _escaped(text, match.start()):
            continue
        start = match.end()
        index, depth, angle = start, 1, False
        while index < len(text) and depth:
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == "<" and index == start:
                angle = True
            elif char == ">" and angle:
                angle = False
            elif not angle:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
            index += 1
        if depth:
            continue
        target = text[start:index - 1].strip()
        if target.startswith("<") and ">" in target:
            target = target[1:target.index(">")]
        else:
            target = target.split(None, 1)[0] if target else ""
        if target:
            yield target
    for match in re.finditer(r"^ {0,3}\[[^]\n^]+\]:\s*(<[^>]+>|\S+)", text, re.M):
        yield match[1].strip("<>")
    for match in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", text, re.I):
        yield match[1]


def document_findings(root, documents, inventory, profile="core", required=()):
    issues, texts = [], {}

    def read(name, mandatory=False):
        if name in texts:
            return texts[name]
        try:
            content = safe_read(root, name)
            text = content.decode("utf-8")
        except (FileNotRead, UnicodeError) as error:
            reason = str(error) if isinstance(error, FileNotRead) else "unsupported_encoding"
            inventory.skip(name, reason)
            code = reason if reason in {"external_symlink", "unresolvable_path"} else "document_not_read"
            issues.append(finding(code, name, "Not read: " + reason + ".",
                                  "error" if mandatory and reason != "file_too_large" else "warning"))
            return None
        texts[name] = text
        if not text.strip():
            issues.append(finding("empty_document", name, "Document is empty.",
                                  "error" if mandatory else "warning"))
        return text

    groups = list(CORE_DOCUMENTS) if profile == "core" else []
    groups.extend((name,) for name in required)
    for alternatives in groups:
        chosen = None
        for name in alternatives:
            try:
                if local_path(root, name).exists():
                    chosen = name
                    break
            except FileNotRead:
                # The inventory/required read reports the boundary, without
                # treating an external file as evidence of a valid document.
                if (root / name).is_symlink():
                    chosen = name
                    break
        if chosen is None:
            issues.append(finding("missing_document", alternatives[0],
                                  "Missing required document; accepted paths: "
                                  + ", ".join(alternatives) + "."))
        else:
            read(chosen, mandatory=True)

    for name in documents:
        text = read(name)
        if text is None:
            continue
        if not is_document(name):
            continue
        for target in dict.fromkeys(link_targets(text)):
            if "{{" in target:
                continue
            target = html.unescape(re.sub(r"\\([" + re.escape(string.punctuation)
                                         + r"])", r"\1", target))
            try:
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                relative = unquote(parsed.path)
                if "\0" in relative:
                    raise ValueError("invalid path")
                path = (Path(relative.lstrip("/")) if relative.startswith("/")
                        else Path(name).parent / relative)
                resolved = local_path(root, path)
                exists = resolved.exists()
            except FileNotRead as error:
                issues.append(finding("external_file_link" if str(error) == "external_symlink"
                                      else "invalid_link", name,
                                      "File target cannot be checked inside this project: "
                                      + public_text(parsed.path) + ".", "warning"))
                continue
            except (OSError, ValueError):
                issues.append(finding("invalid_link", name, "Malformed local file target."))
                continue
            if not exists:
                issues.append(finding("broken_link", name,
                                      "Missing local target: " + public_text(relative)))
    return issues
