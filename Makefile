.PHONY: test check package

test:
	python3 -m unittest discover -s tests -v

check:
	python3 scripts/validate_distribution.py --source-only
	python3 skills/project-init/scripts/project_audit.py check .

package:
	python3 scripts/package_plugin.py
