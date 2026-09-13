"""Shared read-only source contract for packaging and local installation.

The plugin intentionally also serves as a source distribution. Only the
explicitly maintained roots below are payload, never the whole checkout.
"""

from contextlib import ExitStack
import ast
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import sys
import sysconfig
import unicodedata
from urllib.parse import unquote, urlsplit


PLUGIN_NAME = "codex-project-init"
SKILL_NAME = "project-init"
SKILL_ROOT = "skills/" + SKILL_NAME
MANIFEST_PATH = ".codex-plugin/plugin.json"
MARKETPLACE_PATH = ".agents/plugins/marketplace.json"
ROOT_FILES = frozenset({
    MANIFEST_PATH, MARKETPLACE_PATH, "AGENTS.md", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
    "LICENSE", "NOTICE", ".gitignore", ".editorconfig", "Makefile",
})
PAYLOAD_TREES = (SKILL_ROOT, "scripts", "docs", "tests", "assets")
EXCLUDED_NAMES = frozenset({
    "__pycache__", "node_modules", "venv", "env", "dist", "build", "target",
    "out", "htmlcov", "coverage", "site-packages", "cache", "caches", "tmp",
    "temp", "backups", "kubeconfig", "application_default_credentials.json",
    "service-account.json", "service_account.json",
})
EXCLUDED_SUFFIXES = frozenset({
    ".pyc", ".pyo", ".o", ".a", ".so", ".dll", ".dylib", ".class", ".egg",
    ".whl", ".zip", ".tar", ".gz", ".tgz", ".log", ".tmp", ".temp", ".bak",
    ".swp", ".swo", ".orig", ".rej", ".pem", ".key", ".p12", ".pfx", ".jks",
    ".keystore", ".kdbx", ".sqlite", ".sqlite3", ".db", ".tfstate", ".tfplan",
})
CREDENTIAL_CONFIG_SUFFIXES = frozenset({
    "", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".config",
    ".properties", ".xml", ".csv", ".txt", ".env", ".credential", ".credentials",
    ".secret", ".secrets",
})
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


class DistributionError(ValueError):
    """The source or distribution violates the project's payload contract."""


def _safe_name(name):
    if not isinstance(name, str) or not name:
        raise DistributionError("Payload paths must be non-empty relative paths")
    parts = name.split("/")
    if any(not part or part in {".", ".."} or part.rstrip(" .") != part
           for part in parts):
        raise DistributionError("Unsafe payload path: " + repr(name))
    if "\\" in name or ":" in name or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise DistributionError("Unsafe payload path: " + repr(name))
    try:
        name.encode("utf-8")
    except UnicodeError:
        raise DistributionError("Payload paths must be valid UTF-8") from None
    for part in parts:
        stem = part.split(".")[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(COM|LPT)[1-9]", stem):
            raise DistributionError("Non-portable payload path: " + repr(name))


def _excluded(parts):
    for part in parts:
        name = part.casefold()
        suffix = PurePosixPath(name).suffix
        if (name.startswith(".") or name in EXCLUDED_NAMES or name.endswith("~")
                or name.endswith((".egg-info", ".dist-info"))
                or suffix in EXCLUDED_SUFFIXES):
            return True
        if (re.fullmatch(r"(?:credentials?|secrets?)(?:[._-].*)?", name)
                or re.fullmatch(r"id_(?:rsa|dsa|ecdsa|ed25519)(?:\..*)?", name)):
            return True
        # Recognize conventional config names such as client_secret.json and
        # local-credentials.json. This is filename filtering, not content scanning.
        if suffix in CREDENTIAL_CONFIG_SUFFIXES and re.search(
            r"(?:^|[._-])(?:credentials?|secrets?)(?:[._-]|$)", name
        ):
            return True
    return False


def is_payload_path(name):
    """Whether a relative file belongs to the explicit plugin payload."""
    _safe_name(name)
    if name in ROOT_FILES:
        return True
    for tree in PAYLOAD_TREES:
        if name.startswith(tree + "/"):
            return not _excluded(name[len(tree) + 1:].split("/"))
    return False


def _source_root(source):
    root = Path(os.path.abspath(os.fspath(source)))
    try:
        if not stat.S_ISDIR(root.lstat().st_mode):
            raise DistributionError("Source must be a real directory, not a symlink")
        return root.resolve(strict=True)
    except OSError:
        raise DistributionError("Cannot access source directory") from None


def _checked_path(root, relative, directory=False):
    path = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        path = path / part
        try:
            mode = path.lstat().st_mode
        except OSError:
            raise DistributionError("Missing or unreadable payload path: " + relative) from None
        if stat.S_ISLNK(mode):
            raise DistributionError("Payload cannot contain symlinks: " + relative)
        want_directory = index < len(parts) - 1 or directory
        if not (stat.S_ISDIR(mode) if want_directory else stat.S_ISREG(mode)):
            raise DistributionError("Special file or wrong payload path type: " + relative)
    return path


def _collect_paths(root):
    paths = []

    def visit(relative):
        _safe_name(relative)
        path = root / relative
        try:
            mode = path.lstat().st_mode
        except OSError:
            raise DistributionError("Cannot inspect payload path: " + relative) from None
        if stat.S_ISDIR(mode):
            _checked_path(root, relative, directory=True)
            try:
                children = sorted(path.iterdir(), key=lambda entry: entry.name)
            except OSError:
                raise DistributionError("Cannot list payload directory: " + relative) from None
            for child in children:
                if not _excluded((child.name,)):
                    visit(relative + "/" + child.name)
        else:
            paths.append(_checked_path(root, relative))

    for relative in sorted(ROOT_FILES):
        # lexists sees dangling symlinks, which must not disappear silently.
        if os.path.lexists(root / relative):
            paths.append(_checked_path(root, relative))
    for relative in PAYLOAD_TREES:
        if os.path.lexists(root / relative):
            _checked_path(root, relative, directory=True)
            visit(relative)
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def read_regular(root, relative):
    """Read a regular file without following payload links, including parents."""
    _safe_name(relative)
    path = _checked_path(root, relative)
    try:
        with ExitStack() as stack:
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
            if os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW"):
                directory_flags = flags | os.O_NOFOLLOW | os.O_DIRECTORY
                descriptor = os.open(root, directory_flags)
                stack.callback(os.close, descriptor)
                for part in PurePosixPath(relative).parts[:-1]:
                    descriptor = os.open(part, directory_flags, dir_fd=descriptor)
                    stack.callback(os.close, descriptor)
                descriptor = os.open(
                    path.name, flags | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=descriptor,
                )
            else:
                descriptor = os.open(path, flags | getattr(os, "O_NONBLOCK", 0))
            stream = stack.enter_context(os.fdopen(descriptor, "rb"))
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise DistributionError("Payload is no longer a regular file: " + relative)
            current = _checked_path(root, relative).stat()
            if (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino):
                raise DistributionError("Payload changed while being read: " + relative)
            contents = stream.read()
            after = os.fstat(stream.fileno())
            if ((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                    != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                raise DistributionError("Payload changed while being read: " + relative)
            return contents
    except OSError:
        raise DistributionError("Cannot safely read payload file: " + relative) from None


def _text(data, label):
    try:
        return data.decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeError:
        raise DistributionError(label + " must be UTF-8 text") from None


def json_object(data, label):
    """Parse JSON without duplicate keys or non-JSON numeric constants."""
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise DistributionError(label + " contains duplicate JSON keys")
            value[key] = item
        return value

    def constant(_value):
        raise DistributionError(label + " contains a non-JSON numeric constant")

    try:
        value = json.loads(_text(data, label), object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError:
        raise DistributionError(label + " must be valid JSON") from None
    if not isinstance(value, dict):
        raise DistributionError(label + " must contain a JSON object")
    return value


def _without_comment(value):
    quote = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif char == "\\" and quote == '"':
            escaped = True
        elif char == quote:
            quote = None
        elif quote is None and char in "\"'":
            quote = char
        elif quote is None and char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _yaml_scalar(value, label):
    if not value or value in {"null", "Null", "NULL", "~"}:
        return None
    if value.startswith('"'):
        try:
            result = json.loads(value)
        except json.JSONDecodeError:
            raise DistributionError(label + " has an invalid quoted YAML scalar") from None
        if not isinstance(result, str):
            raise DistributionError(label + " has an invalid YAML scalar")
        return result
    if value.startswith("'"):
        if not value.endswith("'") or re.search(r"(?<!')'(?!')", value[1:-1]):
            raise DistributionError(label + " has an invalid quoted YAML scalar")
        return value[1:-1].replace("''", "'")
    if value.startswith(("[", "{")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise DistributionError(label + " uses unsupported flow YAML; use a block mapping/list") from None
    if value.casefold() in {"true", "yes", "on", "false", "no", "off"}:
        return value.casefold() in {"true", "yes", "on"}
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    if value.startswith(("!", "&", "*", "@", "`")) or re.search(r":(?:\s|$)", value):
        raise DistributionError(label + " uses unsupported or invalid YAML scalar syntax")
    return value


def _yaml_mapping(text, label):
    """Read metadata's block YAML without a general YAML runtime dependency.

    Mappings, sequences, quoted/plain scalars and folded/literal text are
    supported. Tags, aliases and non-JSON flow collections are not evaluated.
    """
    tokens = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        prefix = line[:len(line) - len(line.lstrip())]
        if "\t" in prefix:
            raise DistributionError(label + " cannot use tabs for YAML indentation")
        indent = len(prefix)
        value = _without_comment(line[indent:])
        block = re.fullmatch(r"(.*:\s*|-\s+)([|>])([+-]?)", value)
        if block:
            block_lines = []
            while index < len(lines):
                following = lines[index]
                if following.strip() and len(following) - len(following.lstrip()) <= indent:
                    break
                block_lines.append(following)
                index += 1
            nonempty = [item for item in block_lines if item.strip()]
            margin = min((len(item) - len(item.lstrip()) for item in nonempty), default=0)
            content = [item[margin:] for item in block_lines]
            scalar = ("\n" if block.group(2) == "|" else " ").join(content)
            value = block.group(1) + json.dumps(scalar)
        tokens.append((indent, value))

    def parse(position, indent):
        is_list = tokens[position][1] == "-" or tokens[position][1].startswith("- ")
        result = [] if is_list else {}
        while position < len(tokens) and tokens[position][0] >= indent:
            current_indent, value = tokens[position]
            if current_indent != indent:
                raise DistributionError(label + " has inconsistent YAML indentation")
            if is_list:
                if value != "-" and not value.startswith("- "):
                    raise DistributionError(label + " mixes YAML mappings and sequences")
                item = value[1:].strip()
                if re.match(r"[A-Za-z_][A-Za-z0-9_-]*:(?:\s|$)", item):
                    tokens[position] = (indent + 2, item)
                    parsed, position = parse(position, indent + 2)
                elif not item and position + 1 < len(tokens) and tokens[position + 1][0] > indent:
                    parsed, position = parse(position + 1, tokens[position + 1][0])
                else:
                    parsed = _yaml_scalar(item, label)
                    position += 1
                result.append(parsed)
                continue
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?", value)
            if not match:
                raise DistributionError(label + " must use YAML mapping keys")
            key, item = match.group(1), match.group(2) or ""
            if key in result:
                raise DistributionError(label + " contains duplicate YAML keys")
            position += 1
            if not item and position < len(tokens) and tokens[position][0] > indent:
                parsed, position = parse(position, tokens[position][0])
            else:
                parsed = _yaml_scalar(item, label)
            result[key] = parsed
        return result, position

    if not tokens or tokens[0][0] != 0:
        raise DistributionError(label + " must contain a YAML mapping")
    result, end = parse(0, 0)
    if not isinstance(result, dict) or end != len(tokens):
        raise DistributionError(label + " must contain a YAML mapping")
    return result


def _string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(label + " must be a non-empty string")
    return value


def _mapping(value, label):
    if not isinstance(value, dict):
        raise DistributionError(label + " must be an object")
    return value


def _known_keys(value, allowed, label):
    if set(value) - set(allowed):
        raise DistributionError(label + " contains fields unsupported by the bundled plugin schema")


def _asset(value, base, payload, label):
    raw = _string(value, label)
    if raw.startswith("./"):
        raw = raw[2:]
    _safe_name(raw)
    name = base + "/" + raw if base else raw
    if name not in payload:
        raise DistributionError(label + " points to a missing or excluded local resource")


def _https(value, label):
    if value is not None:
        try:
            parsed = urlsplit(_string(value, label))
        except ValueError:
            raise DistributionError(label + " must be an absolute HTTPS URL") from None
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise DistributionError(label + " must be an absolute HTTPS URL without credentials")


def _validate_color(value, label):
    if value is not None and (not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value)):
        raise DistributionError(label + " must use #RRGGBB")


def _validate_manifest(payload):
    manifest = json_object(payload[MANIFEST_PATH], MANIFEST_PATH)
    # Field names/required metadata follow plugin-creator's bundled validator;
    # no category/capability enums or particular prose are required here.
    _known_keys(manifest, {
        "id", "name", "version", "description", "skills", "apps", "mcpServers",
        "interface", "author", "homepage", "repository", "license", "keywords",
    }, "plugin.json")
    if manifest.get("name") != PLUGIN_NAME:
        raise DistributionError("Source is not the expected codex-project-init plugin")
    version = _string(manifest.get("version"), "plugin.json version")
    if not SEMVER.fullmatch(version):
        raise DistributionError("plugin.json version must be strict semver")
    _string(manifest.get("description"), "plugin.json description")
    for field in ("id", "license", "homepage", "repository"):
        if manifest.get(field) is not None:
            _string(manifest[field], "plugin.json " + field)
    if "keywords" in manifest:
        if not isinstance(manifest["keywords"], list):
            raise DistributionError("plugin.json keywords must be an array")
        for value in manifest["keywords"]:
            _string(value, "plugin.json keyword")
    if manifest.get("skills") is not None and manifest["skills"] not in (
        "skills", "skills/", "./skills", "./skills/",
    ):
        raise DistributionError("plugin.json skills must point to ./skills/")
    # This single-skill distribution has no companion app/MCP payload roots.
    for field in ("apps", "mcpServers"):
        if manifest.get(field) is not None:
            if field == "mcpServers" and isinstance(manifest[field], dict):
                for name, configuration in manifest[field].items():
                    _string(name, "MCP server name")
                    _mapping(configuration, "MCP server configuration")
            else:
                raise DistributionError("Declared " + field + " companion is not in this payload")
    author = _mapping(manifest.get("author"), "plugin.json author")
    _known_keys(author, {"name", "email", "url"}, "plugin.json author")
    _string(author.get("name"), "plugin.json author.name")
    if author.get("email") is not None:
        _string(author["email"], "plugin.json author.email")
    _https(author.get("url"), "plugin.json author.url")
    interface = _mapping(manifest.get("interface"), "plugin.json interface")
    _known_keys(interface, {
        "displayName", "shortDescription", "longDescription", "developerName",
        "category", "capabilities", "websiteURL", "privacyPolicyURL",
        "termsOfServiceURL", "brandColor", "composerIcon", "logo", "logoDark",
        "screenshots", "defaultPrompt", "default_prompt",
    }, "plugin.json interface")
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        _string(interface.get(field), "plugin.json interface." + field)
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list):
        raise DistributionError("plugin.json interface.capabilities must be an array")
    for value in capabilities:
        _string(value, "plugin.json interface capability")
    prompts = [interface[key] for key in ("defaultPrompt", "default_prompt") if key in interface]
    if not prompts:
        raise DistributionError("plugin.json interface must declare defaultPrompt or default_prompt")
    for prompt in prompts:
        for value in prompt if isinstance(prompt, list) else [prompt]:
            _string(value, "plugin.json interface default prompt")
    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        _https(interface.get(field), "plugin.json interface." + field)
    _validate_color(interface.get("brandColor"), "plugin.json interface.brandColor")
    for field in ("composerIcon", "logo", "logoDark"):
        if interface.get(field) is not None:
            _asset(interface[field], "", payload, "plugin.json interface." + field)
    screenshots = interface.get("screenshots", [])
    if not isinstance(screenshots, list):
        raise DistributionError("plugin.json interface.screenshots must be an array")
    for value in screenshots:
        _asset(value, "", payload, "plugin.json screenshot")

    def placeholders(value):
        if isinstance(value, str) and "[TODO:" in value:
            raise DistributionError("plugin.json contains an unfinished metadata placeholder")
        if isinstance(value, (dict, list)):
            for item in value.values() if isinstance(value, dict) else value:
                placeholders(item)

    placeholders(manifest)
    return manifest


def _validate_marketplace(payload, manifest):
    """Keep the native catalogue self-contained with this single-plugin source."""
    catalogue = json_object(payload[MARKETPLACE_PATH], MARKETPLACE_PATH)
    _known_keys(catalogue, {"name", "interface", "plugins"}, "marketplace.json")
    name = _string(catalogue.get("name"), "marketplace.json name")
    if re.fullmatch(r"[A-Za-z0-9_-]+", name) is None:
        raise DistributionError("marketplace.json name must be a marketplace identifier")
    if "interface" in catalogue:
        interface = _mapping(catalogue["interface"], "marketplace.json interface")
        _known_keys(interface, {"displayName"}, "marketplace.json interface")
        _string(interface.get("displayName"), "marketplace.json interface.displayName")
    entries = catalogue.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        raise DistributionError("Marketplace must contain the bundled plugin exactly once")
    entry = _mapping(entries[0], "marketplace plugin")
    _known_keys(entry, {"name", "source", "policy", "category"}, "marketplace plugin")
    if entry.get("name") != manifest["name"]:
        raise DistributionError("Marketplace plugin must match the bundled plugin manifest")
    if entry.get("source") != {"source": "local", "path": "./"}:
        raise DistributionError("Marketplace must reference the bundled plugin root with ./")
    _string(entry.get("category"), "marketplace plugin category")
    policy = _mapping(entry.get("policy"), "marketplace plugin policy")
    _known_keys(policy, {"installation", "authentication"}, "marketplace plugin policy")
    installation = _string(policy.get("installation"), "marketplace installation policy")
    authentication = _string(policy.get("authentication"), "marketplace authentication policy")
    if installation not in {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}:
        raise DistributionError("Marketplace has an invalid installation policy")
    if authentication not in {"ON_INSTALL", "ON_USE"}:
        raise DistributionError("Marketplace has an invalid authentication policy")


def _without_fences(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, rest = match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not rest.strip():
                fence = None
            continue
        if fence is None and not line.startswith(("    ", "\t")):
            lines.append(line)
    return re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)


def _link_destination(text, start):
    if start < len(text) and text[start] == "<":
        end = text.find(">", start + 1)
        return text[start + 1:end] if end != -1 else ""
    depth = 0
    end = start
    while end < len(text):
        char = text[end]
        if char == "\\" and end + 1 < len(text):
            end += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        elif char.isspace() and depth == 0:
            break
        end += 1
    return re.sub(r"\\([() ])", r"\1", text[start:end])


def _local_reference(raw, origin, payload, base=None):
    raw = html.unescape(raw)
    if not raw or raw.startswith("#") or any(marker in raw for marker in ("{{", "}}", "<", ">")):
        return
    try:
        parsed = urlsplit(raw)
    except ValueError:
        raise DistributionError(origin + " contains an invalid resource link") from None
    if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or raw.startswith("//"):
        return
    if parsed.scheme or parsed.netloc:
        raise DistributionError(origin + " contains a non-portable resource link")
    path = unquote(parsed.path)
    if not path:
        return
    if path.startswith("/") or "\\" in path:
        raise DistributionError(origin + " contains an absolute or unsafe local resource link")
    parts = (base or str(PurePosixPath(origin).parent)).split("/")
    for part in path.split("/"):
        if part == "..":
            if len(parts) <= len(PurePosixPath(SKILL_ROOT).parts):
                raise DistributionError(origin + " references a resource outside the standalone skill")
            parts.pop()
        elif part not in {"", "."}:
            parts.append(part)
    name = "/".join(parts)
    _safe_name(name)
    if name not in payload and not any(item.startswith(name + "/") for item in payload):
        raise DistributionError(origin + " references a missing or excluded skill resource: " + name)


def _declared_bindings(tree, ignored_import=None):
    """Collect module-level bindings without evaluating values or nested scopes."""
    names = {"__name__", "__doc__", "__package__", "__loader__", "__spec__"}
    pending = list(tree.body)
    while pending:
        node = pending.pop()
        if node is ignored_import:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names if alias.name != "*")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.AnnAssign) and node.value is None:
            # An annotation alone does not bind the name at runtime.
            continue
        elif isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            continue
        else:
            pending.extend(ast.iter_child_nodes(node))
    return names


def _validate_python_scripts(payload):
    """Resolve static local imports without importing or running skill code."""
    scripts_root = SKILL_ROOT + "/scripts"
    trees = {}
    for name, data in payload.items():
        if name.startswith(scripts_root + "/") and name.endswith(".py"):
            try:
                trees[name] = ast.parse(data, filename=name, feature_version=9)
            except (SyntaxError, ValueError):
                raise DistributionError(name + " is not valid Python 3.9 source") from None
    stdlib = Path(sysconfig.get_path("stdlib"))

    def module_exists(name):
        return (name + ".py" in trees or name + "/__init__.py" in trees
                or any(path.startswith(name + "/") for path in trees))

    def standard_library(name):
        # sys.stdlib_module_names is unavailable on supported Python 3.9.
        return (name in sys.builtin_module_names or (stdlib / (name + ".py")).is_file()
                or (stdlib / name).is_dir()
                or any((stdlib / "lib-dynload").glob(name + ".*")))

    declared = {name: _declared_bindings(tree) for name, tree in trees.items()}

    for name, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            relative = isinstance(node, ast.ImportFrom) and node.level
            modules = [node.module or ""] if isinstance(node, ast.ImportFrom) else [
                alias.name for alias in node.names
            ]
            for module in modules:
                if relative:
                    parts = list(PurePosixPath(name).parent.parts)
                    if node.level > len(parts) - len(PurePosixPath(scripts_root).parts):
                        raise DistributionError(name + " has an import outside its script package")
                    base = "/".join(parts[:len(parts) - node.level + 1])
                    target = base + "/" + module.replace(".", "/") if module else base
                else:
                    root_module = module.split(".")[0]
                    if not module_exists(scripts_root + "/" + root_module) and standard_library(root_module):
                        continue
                    target = scripts_root + "/" + module.replace(".", "/")
                if not module_exists(target):
                    raise DistributionError(name + " imports a missing local script module: " + module)
                if not isinstance(node, ast.ImportFrom):
                    continue
                initializer = target + "/__init__.py"
                module_file = target + ".py"
                target_file = initializer if initializer in trees else module_file
                is_package = initializer in trees or module_file not in trees
                bindings = declared.get(target_file, {
                    "__name__", "__doc__", "__package__", "__loader__", "__spec__",
                })
                if target_file == name:
                    # `from . import worker` in __init__.py cannot serve as
                    # proof of its own export after worker.py disappears.
                    bindings = _declared_bindings(tree, ignored_import=node)
                if target_file in trees:
                    bindings = bindings | {"__file__", "__cached__", "__builtins__"}
                if is_package:
                    bindings = bindings | {"__path__"}
                for alias in node.names:
                    if alias.name == "*" or alias.name in bindings:
                        continue
                    if is_package and module_exists(target + "/" + alias.name):
                        continue
                    raise DistributionError(
                        name + " imports a missing submodule or declared symbol: " + alias.name
                    )


def _validate_skill(payload):
    skill_path = SKILL_ROOT + "/SKILL.md"
    contents = _text(payload[skill_path], skill_path)
    lines = contents.splitlines()
    if not lines or lines[0].strip() != "---":
        raise DistributionError("SKILL.md must begin with YAML frontmatter")
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise DistributionError("SKILL.md frontmatter is not closed")
    metadata = _yaml_mapping("\n".join(lines[1:end]), "SKILL.md frontmatter")
    if metadata.get("name") != SKILL_NAME:
        raise DistributionError("SKILL.md name must be project-init")
    _string(metadata.get("description"), "SKILL.md description")
    _validate_python_scripts(payload)
    for field in ("disable-model-invocation", "disable_model_invocation"):
        if metadata.get(field) is not None and metadata[field] is not False:
            raise DistributionError("SKILL.md " + field + " must be false when present")
    agent_path = SKILL_ROOT + "/agents/openai.yaml"
    if agent_path in payload:
        agent = _yaml_mapping(_text(payload[agent_path], agent_path), agent_path)
        _known_keys(agent, {"interface", "policy", "dependencies"}, agent_path)
        interface = _mapping(agent.get("interface"), agent_path + " interface")
        _known_keys(interface, {
            "display_name", "short_description", "icon_small", "icon_large",
            "brand_color", "default_prompt",
        }, agent_path + " interface")
        for field in ("display_name", "short_description"):
            _string(interface.get(field), agent_path + " " + field)
        if interface.get("default_prompt") is not None:
            _string(interface["default_prompt"], agent_path + " default_prompt")
        _validate_color(interface.get("brand_color"), agent_path + " brand_color")
        for field in ("icon_small", "icon_large"):
            if interface.get(field) is not None:
                _asset(interface[field], SKILL_ROOT, payload, agent_path + " " + field)
        if agent.get("policy") is not None:
            policy = _mapping(agent["policy"], agent_path + " policy")
            _known_keys(policy, {"allow_implicit_invocation"}, agent_path + " policy")
            if (policy.get("allow_implicit_invocation") is not None
                    and not isinstance(policy["allow_implicit_invocation"], bool)):
                raise DistributionError(agent_path + " allow_implicit_invocation must be boolean")
        if agent.get("dependencies") is not None:
            _known_keys(_mapping(agent["dependencies"], agent_path + " dependencies"),
                        {"tools"}, agent_path + " dependencies")
    for name, data in payload.items():
        if not name.startswith(SKILL_ROOT + "/"):
            continue
        if not name.endswith(".md"):
            continue
        text = _without_fences(_text(data, name))
        # Backtick resource paths in authoring guides are skill-relative.
        for match in re.finditer(r"`((?:assets|references|scripts|agents)/[^`\n]*)`", text):
            resource = match.group(1)
            if resource.startswith("scripts/") and SKILL_ROOT + "/" + resource not in payload:
                # Keep complete literal filenames with spaces. For commands,
                # inspect only the script token; arguments can name a target project.
                lexer = shlex.shlex(resource, posix=True)
                lexer.whitespace_split = True
                lexer.commenters = ""
                try:
                    resource = next(lexer)
                except (ValueError, StopIteration):
                    raise DistributionError(name + " contains an invalid inline script path") from None
            _local_reference(resource, name, payload, base=SKILL_ROOT)
        text = re.sub(r"(`+).*?\1", "", text)
        for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*", text):
            _local_reference(_link_destination(text, match.end()), name, payload)
        for match in re.finditer(r"(?m)^ {0,3}\[[^\]\n]+\]:\s*", text):
            _local_reference(_link_destination(text, match.end()), name, payload)
        for match in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", text, flags=re.I):
            _local_reference(match.group(1), name, payload)


def validate_payload(payload):
    """Validate captured plugin files without executing any bundled code."""
    if not isinstance(payload, dict):
        raise DistributionError("Plugin payload must be a file mapping")
    collisions = set()
    for name in payload:
        if not is_payload_path(name):
            raise DistributionError("File is outside the explicit payload: " + name)
        portable = unicodedata.normalize("NFC", name).casefold()
        if portable in collisions:
            raise DistributionError("Payload paths collide on case-insensitive filesystems")
        collisions.add(portable)
    for required in (MANIFEST_PATH, MARKETPLACE_PATH,
                     SKILL_ROOT + "/SKILL.md", SKILL_ROOT + "/scripts/project_audit.py"):
        if required not in payload:
            raise DistributionError("Missing required payload file: " + required)
    manifest = _validate_manifest(payload)
    _validate_marketplace(payload, manifest)
    _validate_skill(payload)
    return manifest


def source_snapshot(source):
    """Return one validated byte snapshot for both archives, with its manifest."""
    root = _source_root(source)
    payload = {
        path.relative_to(root).as_posix(): read_regular(root, path.relative_to(root).as_posix())
        for path in _collect_paths(root)
    }
    return validate_payload(payload), payload


def validate_source(source: Path) -> dict:
    """Validate the expected plugin and all included local skill resources."""
    manifest, _payload = source_snapshot(source)
    return manifest


def payload_files(source: Path) -> list[Path]:
    """Return sorted absolute regular source paths in a validated PLUGIN payload.

    Callers must preserve their relative paths when copying. No target code is
    executed, and no filesystem writes are performed by this function.
    """
    root = _source_root(source)
    _manifest, payload = source_snapshot(root)
    return [_checked_path(root, name) for name in sorted(payload)]
