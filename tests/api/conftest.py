from __future__ import annotations

import json
import os
import uuid
import warnings
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from _pytest.reports import TestReport
from _pytest.runner import CallInfo

from caldiy_qa.builders import UniqueNames
from caldiy_qa.cleanup import CleanupStack
from caldiy_qa.client import CalDiyClient
from caldiy_qa.config import Settings
from caldiy_qa.contracts import ContractValidator
from caldiy_qa.factories import ResourceFactory


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: CallInfo[None]) -> Generator[None, None, None]:
    outcome = yield
    report: TestReport = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def worker_id() -> str:
    return os.getenv("PYTEST_XDIST_WORKER", "main")


@pytest.fixture(scope="session")
def run_id() -> str:
    supplied = os.getenv("QA_RUN_ID")
    if supplied:
        return supplied
    return f"{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def contracts(worker_id: str) -> Generator[ContractValidator, None, None]:
    validator = ContractValidator.load()
    validator.validate_documents()
    yield validator
    report_dir = Path("test-results/api")
    report_dir.mkdir(parents=True, exist_ok=True)
    omissions = [
        {"path": path, "method": method.upper(), "status": status}
        for path, method, status in sorted(validator.omissions)
    ]
    (report_dir / f"contract-omissions-{worker_id}.json").write_text(
        json.dumps(
            {
                "worker": worker_id,
                "omissions": omissions,
                "knownSchemaDeviations": [
                    {"finding": finding, "operation": operation, "path": path}
                    for finding, operation, path in sorted(validator.schema_deviations)
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def api_client(settings: Settings, contracts: ContractValidator) -> Generator[CalDiyClient, None, None]:
    with CalDiyClient(settings, contracts) as client:
        yield client


@pytest.fixture
def names(run_id: str, worker_id: str) -> UniqueNames:
    return UniqueNames(run_id=run_id, worker_id=worker_id)


@pytest.fixture
def cleanup_stack(request: pytest.FixtureRequest) -> Generator[CleanupStack, None, None]:
    stack = CleanupStack()
    yield stack
    failures = stack.close()
    if not failures:
        return
    detail = "\n".join(f"{failure.label}: {failure.error}" for failure in failures)
    request.node.add_report_section("teardown", "cleanup failures", detail)
    call_report = getattr(request.node, "rep_call", None)
    if call_report is not None and call_report.failed:
        warnings.warn(
            pytest.PytestWarning(f"Cleanup also failed after the original test failure:\n{detail}"),
            stacklevel=2,
        )
    else:
        pytest.fail(f"Fixture cleanup failed:\n{detail}", pytrace=False)


@pytest.fixture
def resources(
    api_client: CalDiyClient,
    names: UniqueNames,
    cleanup_stack: CleanupStack,
) -> ResourceFactory:
    return ResourceFactory(client=api_client, names=names, cleanup=cleanup_stack)
