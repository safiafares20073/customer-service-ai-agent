import json
import subprocess
import sys
from decimal import Decimal


def worker(mode, database, token, evidence, task_id=None):
    command = [sys.executable, "-m", "tests.agent_worker", mode, str(database.path), str(evidence)]
    if task_id:
        command += ["--task-id", task_id]
    result = subprocess.run(
        command, input=token, capture_output=True, text=True, timeout=30, check=True
    )
    return json.loads(result.stdout)


def test_conversation_fact_survives_agent_process_exit_without_cross_customer_leak(
    database,
    store,
    tokens,
    tmp_path,
):
    first = worker("remember", database, tokens["demo-a"], tmp_path / "evidence")
    assert first["status"] == "completed" and first["provider"] == "fixture"
    new_session_a = store.provision_demo_session(
        "demo-a", enable_demo_auth=True, app_env="development"
    )
    second = worker("recall", database, new_session_a, tmp_path / "evidence")
    other = worker("recall", database, tokens["demo-b"], tmp_path / "evidence")
    assert second["status"] == "completed" and "wired headphones" in second["answer"]
    assert other["status"] == "completed" and "wired headphones" not in other["answer"]
    assert first["task_id"] != second["task_id"] != other["task_id"]


def test_ticket_confirmation_resumes_same_task_after_agent_process_exit(
    database,
    store,
    tokens,
    tmp_path,
):
    first = worker("ticket_start", database, tokens["demo-a"], tmp_path / "evidence")
    assert first["status"] == "awaiting_confirmation" and first["turns"] == 1
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
    second = worker(
        "ticket_resume", database, tokens["demo-a"], tmp_path / "evidence", first["task_id"]
    )
    assert second["status"] == "completed" and second["turns"] == 2
    assert second["task_id"] == first["task_id"]
    assert second["requests_this_process"] == 1
    assert second["active_seconds"] >= first["active_seconds"]
    assert Decimal(second["cost_usd"]) > Decimal(first["cost_usd"])
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
        rows = conn.execute("SELECT task_id, provider FROM cost_records").fetchall()
        assert [tuple(row) for row in rows] == [(first["task_id"], "fixture")] * 2
