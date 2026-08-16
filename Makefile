# SPDX-License-Identifier: MPL-2.0

SHELL := /bin/sh

ifeq ($(origin CC),default)
CC := clang
endif

PYTHON ?= python3
BUILD_DIR ?= build
FIRMWARE ?= 1.30
MODULES ?=
MODULE_GUARDS := $(wildcard mod/modules/*/$(FIRMWARE)/test_regressions.py)
AUTOEXEC := $(BUILD_DIR)/autoexec.bin
PATCH_ARGS := $(foreach patch,$(MODULES),--patch $(patch))

.DEFAULT_GOAL := help

.PHONY: help hook autoexec app test preflight clean

help:
	@printf '%s\n' \
	  'make hook                         no-op until AZ rbp offsets are mapped' \
	  'make autoexec KEY=/path/key       build the default firmware 1.30 runtime' \
	  'make autoexec KEY=... MODULES="probe logging"' \
	  'make app                          open the XDJ-AZ Toolkit' \
	  'make test                         run source tests' \
	  'make preflight                    inspect publishable files' \
	  'make clean                        remove build/ only'

# Firmware 1.30 has no mapped rbp hook. Compiling the RX3 ARM32 core against
# an aarch64 player would be unsafe even as a build check, so this target
# records the skip instead of producing a shared object.
hook:
	@mkdir -p "$(BUILD_DIR)"
	@echo 'AZ firmware $(FIRMWARE) has no mapped rbp hook; not compiling one.' \
	  | tee "$(BUILD_DIR)/hook-skipped.txt"

autoexec:
	@test -n "$(KEY)" || { echo 'KEY=/path/outside/the-repository/aes256.key is required' >&2; exit 2; }
	@test -f "$(KEY)" || { echo 'key not found: $(KEY)' >&2; exit 2; }
	@mkdir -p "$(BUILD_DIR)"
	$(PYTHON) tools/rx3_runtime/cli.py build \
	  --firmware "$(FIRMWARE)" $(PATCH_ARGS) --key "$(KEY)" --output "$(BUILD_DIR)"

app:
	$(PYTHON) apps/rx3-toolbox/main.py

test:
	@set -e; for guard in $(MODULE_GUARDS); do $(PYTHON) "$$guard"; done
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

preflight:
	./scripts/preflight.sh

clean:
	rm -rf "$(BUILD_DIR)"
