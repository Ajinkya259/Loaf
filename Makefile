# Loaf — common tasks. `make help` for the list.

BLENDER ?= /Applications/Blender.app/Contents/MacOS/Blender
SHELL   := /bin/zsh

.PHONY: help build run stop cat contact clean

help:
	@echo "Loaf tasks:"
	@echo "  make build     - swift build"
	@echo "  make run       - build, kill any running copy, launch her on the dock"
	@echo "  make stop      - quit her"
	@echo "  make cat       - rebuild every sprite from Blender (both poses + previews)"
	@echo "  make contact   - open the contact sheet for review"
	@echo "  make clean     - remove build artifacts"
	@echo ""
	@echo "Inspect one state without clicking through the menu:"
	@echo "  LOAF_STATE=sit make run       (idle | walk | look | sit)"

build:
	swift build

run: build
	@pkill -x Loaf 2>/dev/null; true
	@./.build/debug/Loaf &

stop:
	@pkill -x Loaf 2>/dev/null; true

# Rebuilds BOTH poses. Never run one build script alone - that is how the standing
# and sitting cats drifted apart twice. See CLAUDE.md §3.
cat:
	./blender/build_all.sh

contact:
	open blender/previews/contact_sheet.png

clean:
	rm -rf .build
