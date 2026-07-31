SHELL := /usr/bin/env bash

.PHONY: help api-build sut-bootstrap sut-smoke sut-api-bootstrap sut-api-smoke sut-down sut-reset test-bootstrap test-api contracts-verify validate

help:
	@printf '%s\n' \
	  'make api-build                             Build private local API v2 image from exact source' \
	  'make sut-bootstrap                         Start, migrate and seed Cal.diy' \
	  'make sut-smoke                             Check database, web and mail services' \
	  'make sut-api-bootstrap                     Start and qualify the complete API v2 stack' \
	  'make sut-api-smoke                         Check API v2, Redis, docs and seed authentication' \
	  'make sut-down                              Stop services and preserve data' \
	  'make sut-reset CONFIRM=caldiy-qa-strategy  Delete this project data and rebuild' \
	  'make test-bootstrap                        Install locked Python 3.12 test dependencies' \
	  'make test-api                              Run the isolated API v2 suite with reports' \
	  'make contracts-verify                      Verify pinned and live suite operation contracts' \
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

test-bootstrap:
	@./scripts/test-bootstrap.sh

test-api:
	@./scripts/test-api.sh

contracts-verify:
	@./scripts/contracts-verify.sh

validate:
	@./scripts/validate.sh
