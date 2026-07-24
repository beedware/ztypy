PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
TARGET ?= ztypy

.PHONY: install uninstall run test

install:
	uv tool install --reinstall .

uninstall:
	uv tool uninstall $(TARGET)

run:
	uv run ztypy $(ARGS)

test:
	uv run python -m unittest discover -s tests -v
