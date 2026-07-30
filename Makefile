SHELL := /usr/bin/env bash

.PHONY: help sut-bootstrap sut-smoke sut-down sut-reset validate

help:
	@printf '%s\n' \
	  'make sut-bootstrap                         Start, migrate and seed Cal.diy' \
	  'make sut-smoke                             Check database, web and mail services' \
	  'make sut-down                              Stop services and preserve data' \
	  'make sut-reset CONFIRM=caldiy-qa-strategy  Delete this project data and rebuild' \
	  'make validate                              Run Phase 1 static validation'

sut-bootstrap:
	@./scripts/bootstrap.sh

sut-smoke:
	@./scripts/smoke.sh

sut-down:
	@./scripts/compose.sh down

sut-reset:
	@CONFIRM='$(CONFIRM)' ./scripts/reset.sh

validate:
	@./scripts/validate.sh
