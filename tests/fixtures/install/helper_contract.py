"""Independent CLI double for only the helper operations used by the installer.

Tests copy this file to each helper's command name. It intentionally omits
scaffold options, naming rules, and schema validation owned by Codex. Optional
integration tests exercise installed Codex helpers separately.
"""

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
command = Path(__file__).name
if command == "create_basic_plugin.py":
    parser.add_argument("plugin_name")
    parser.add_argument("--path", required=True)
    parser.add_argument("--with-marketplace", action="store_true", required=True)
    parser.add_argument("--marketplace-path", required=True)
elif command == "read_marketplace_name.py":
    parser.add_argument("--marketplace-path", required=True)
elif command == "update_plugin_cachebuster.py":
    parser.add_argument("plugin_path")
else:
    raise SystemExit("Unexpected helper command")
args = parser.parse_args()

if command == "read_marketplace_name.py":
    print(json.loads(Path(args.marketplace_path).read_text())["name"])
elif command == "update_plugin_cachebuster.py":
    manifest = Path(args.plugin_path) / ".codex-plugin/plugin.json"
    payload = json.loads(manifest.read_text())
    payload["version"] = payload["version"].split("+", 1)[0] + "+codex.fixture-update"
    manifest.write_text(json.dumps(payload) + "\n")
else:
    marketplace = Path(args.marketplace_path)
    payload = json.loads(marketplace.read_text()) if marketplace.exists() else {
        "name": "personal", "interface": {"displayName": "Personal"}, "plugins": [],
    }
    if any(entry["name"] == args.plugin_name for entry in payload["plugins"]):
        raise SystemExit("Duplicate fixture entry")
    payload["plugins"].append({
        "name": args.plugin_name,
        "source": {"source": "local", "path": "./plugins/" + args.plugin_name},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    })
    manifest = Path(args.path) / args.plugin_name / ".codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": args.plugin_name, "version": "0.1.0"}))
    marketplace.parent.mkdir(parents=True, exist_ok=True)
    marketplace.write_text(json.dumps(payload) + "\n")
