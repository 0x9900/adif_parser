#
# vim:ft=make
# fred, 2026-05-28 21:43
#
#
## Makefile for adif_parser Python module

.PHONY: clean pre-commit mypy pylint build

# Clean: Remove build artifacts and cache
clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .mypy_cache/ .pylint.py

# Pre-commit: Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Mypy: Run static type checking
mypy:
	mypy adif_parser/

# Pylint: Run code linting
pylint:
	pylint adif_parser/

# Build: Build the Python package
build: clean
	python -m build
