import json
import os
from pathlib import Path

import pytest

from tests.trace_scenarios import run_scenario
from yemen_customer_service.agent.provider import OpenAIProvider


@pytest.fixture
def scenario_root():
    # Retain reports/databases even after pytest rotates temporary directories.
    return Path(os.getenv("TRACE_SCENARIO_EVIDENCE", "artifacts/phase5-trace-fixtures/pytest"))


@pytest.mark.parametrize("scenario", ["near_failure_recovery", "explicit_failure"])
async def test_actual_fixture_scenarios_reconcile(scenario_root, monkeypatch, scenario):
    def paid_forbidden(*args, **kwargs):
        raise AssertionError("No live provider allowed")

    monkeypatch.setattr(OpenAIProvider, "from_environment", paid_forbidden)
    directory, report = await run_scenario(scenario_root, scenario)
    assert report["result"] == "PASS", report["checks"]
    assert all(report["checks"].values())
    assert json.loads((directory / "report.json").read_text()) == report
    assert report["fixture_usage_not_billed"] is True
    assert report["fixture_computed_usd"] == (
        "0.00004" if scenario == "near_failure_recovery" else "0.00002"
    )
    _, second = await run_scenario(scenario_root, scenario)
    assert second["result"] == "PASS"
    assert second["task_id"] != report["task_id"]  # Never overwrite/rerun an old task.


@pytest.mark.parametrize(
    ("fault", "calls", "status"),
    [
        ("always", 2, "internal_error"),
        ("nonretryable", 1, "internal_error"),
        ("denied", 1, "access_denied"),
    ],
)
async def test_recovery_does_not_hide_persistent_or_security_faults(
    scenario_root, fault, calls, status
):
    directory, report = await run_scenario(scenario_root, "near_failure_recovery", fault=fault)
    # These deliberate negative controls fail the recovery acceptance, as recorded.
    assert report["result"] == "FAIL"
    assert report["status"] == status
    assert report["turns"] == 1
    assert len([a for a in report["audit_records"] if a["tool"] == "list_products"]) == calls
    assert report["checks"]["no_writes_or_consent"]
    assert report["checks"]["limits_retained"]
    assert json.loads((directory / "report.json").read_text())["result"] == "FAIL"


async def test_recovery_respects_agent_tool_timeout(scenario_root):
    _, report = await run_scenario(scenario_root, "near_failure_recovery", tool_seconds=0.000001)
    assert report["result"] == "FAIL"  # Deliberately impossible timeout, retained.
    assert report["status"] == "tool_timeout"
    assert report["turns"] == 1
    assert report["checks"]["no_writes_or_consent"]


async def test_fixture_harness_refuses_submission_destination(tmp_path):
    with pytest.raises(ValueError, match="submission"):
        await run_scenario(tmp_path / "traces", "explicit_failure")
    assert not (tmp_path / "traces").exists()
