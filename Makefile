.PHONY: import_external import_yaml generate launch test lint

# Import data from outside sources (customize this command)
import_external:
	@echo "Importing from outside sources..."
	uv run bible-atlas/import_external.py

# Import from YAML files (customize this command)
import_yaml:
	@echo "Importing from YAML files..."
	uv run bible-atlas/import_yaml.py

generate:
	uv run bible-atlas/md_generator.py

launch:
	uv sync
	uv run -m mkdocs serve

test:
	uv sync
	uv run -m pytest

lint:
	uv sync
	uv run -m flake8 scripts/

clean:
	rm -rf site/ .uv/ .mypy_cache/ .pytest_cache/ __pycache__/ docs/en/person docs/en/place docs/en/tribe docs/en/theme