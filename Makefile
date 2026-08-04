SHELL := /usr/bin/env bash

.PHONY: help api-build sut-bootstrap sut-smoke sut-api-bootstrap sut-api-smoke sut-down sut-reset test-bootstrap test-api test-e2e test-timezones test-bdd test-a11y update-snapshots perf-baseline test-perf test-contention contracts-verify defects-audit validate

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
	  'make test-e2e                              Run Chromium lifecycle and Firefox smoke tests' \
	  'make test-timezones                        Run the pinned-oracle timezone matrix' \
	  'make test-bdd                              Run exactly three Cucumber lifecycle journeys' \
	  'make test-a11y                             Run serious/critical axe checks' \
	  'make update-snapshots CONFIRM=caldiy-qa-strategy  Explicitly update Chromium snapshots' \
	  'make perf-baseline                         Measure five local availability runs' \
	  'make test-perf                             Run availability and booking throughput gates' \
	  'make test-contention                       Verify one winner under 20-way slot contention' \
	  'make contracts-verify                      Verify pinned and live suite operation contracts' \
	  'make defects-audit                         Audit current public main without testing hosted Cal.com' \
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

test-e2e:
	@./scripts/browser-test.sh e2e

test-timezones:
	@./scripts/browser-test.sh timezones

test-bdd:
	@./scripts/browser-test.sh bdd

test-a11y:
	@./scripts/browser-test.sh a11y

update-snapshots:
	@CONFIRM='$(CONFIRM)' ./scripts/update-snapshots.sh

perf-baseline:
	@./scripts/perf-baseline.sh

test-perf:
	@./scripts/perf-test.sh

test-contention:
	@./scripts/perf-contention.sh

contracts-verify:
	@./scripts/contracts-verify.sh

defects-audit:
	@./scripts/current-defect-audit.sh

validate:
	@./scripts/validate.sh
