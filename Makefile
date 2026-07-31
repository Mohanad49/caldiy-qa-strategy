SHELL := /usr/bin/env bash

.PHONY: help api-build sut-bootstrap sut-smoke sut-api-bootstrap sut-api-smoke sut-down sut-reset validate

help:
	@printf '%s\n' \
	  'make api-build                             Build private local API v2 image from exact source' \
	  'make sut-bootstrap                         Start, migrate and seed Cal.diy' \
	  'make sut-smoke                             Check database, web and mail services' \
	  'make sut-api-bootstrap                     Start and qualify the complete API v2 stack' \
	  'make sut-api-smoke                         Check API v2, Redis, docs and seed authentication' \
	  'make sut-down                              Stop services and preserve data' \
	  'make sut-reset CONFIRM=caldiy-qa-strategy  Delete this project data and rebuild' \
	  'make validate                              Run repository static validation'

api-build:
	@./scripts/api-build.sh

sut-bootstrap:
	@./scripts/bootstrap.sh

sut-smoke:
	@./scripts/smoke.sh

sut-api-bootstrap:
	@./scripts/api-bootstrap.sh

sut-api-smoke:
	@./scripts/api-smoke.sh

sut-down:
	@./scripts/compose.sh --profile api down

sut-reset:
	@CONFIRM='$(CONFIRM)' ./scripts/reset.sh

validate:
	@./scripts/validate.sh
