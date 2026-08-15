.PHONY: install quality fetch build all

install:
	python -m pip install -e '.[dev]'

quality:
	ruff check .
	ruff format --check .
	mypy src
	pytest

fetch:
	hizmet-nabiz fetch

build:
	hizmet-nabiz build

all:
	hizmet-nabiz all
