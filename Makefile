.PHONY: install fmt lint test

install:
	python -m pip install -U pip
	python -m pip install -U pytest
	python -m pip install -U pre-commit black isort flake8 flake8-bugbear flake8-comprehensions

fmt:
	black .
	isort .

lint:
	flake8 .
	pre-commit run --all-files

test:
	pytest -q
