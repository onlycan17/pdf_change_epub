PYTHON ?= python3
CODE_DIRS := app tests

.PHONY: fmt lint test check

fmt:
	$(PYTHON) -m black $(CODE_DIRS)
	$(PYTHON) -m ruff check --fix $(CODE_DIRS)

lint:
	$(PYTHON) -m ruff check $(CODE_DIRS)
	$(PYTHON) -m mypy $(CODE_DIRS)

test:
	$(PYTHON) -m pytest

check: fmt lint test
