.PHONY: test check package install-skill install-plugin

test:
	python3 -m unittest discover -s tests -v

check:
	python3 scripts/validate_distribution.py --source-only
	python3 skills/project-init/scripts/project_audit.py check .

package:
	python3 scripts/package_plugin.py

install-skill:
	python3 scripts/install.py --mode skill

install-plugin:
	python3 scripts/install.py --mode plugin
