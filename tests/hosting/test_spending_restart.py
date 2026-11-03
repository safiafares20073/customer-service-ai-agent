import os
import subprocess
import sys
import time
from dataclasses import replace
from decimal import Decimal

import pytest

from yemen_customer_service.agent.pricing import Pricing, Usage
from yemen_customer_service.agent.provider import ProviderError
from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.spending import Spending, single_operation
from yemen_customer_service.tool_server.models import SafeError


def settle(store, token, amount, *, usage=None):
    price = Pricing.load("config/model_pricing.json", "gpt-6-luna")
    spend = Spending(store, token)
    ident = spend.reserve(Decimal(amount), price, "fixture")
    spend.reconcile(ident, price, usage, bound=1_000_000, output_limit=512)
    return ident


def test_global_and_principal_caps_do_not_reset_with_new_login(
    hosted_store, enabled, claims, login
):
    cfg = replace(enabled, global_budget=Decimal("0.05"), principal_budget=Decimal("0.05"))
    hosted_store.configure(cfg)
    first = hosted_store.provision(login, tasks_per_hour=5)
    settle(hosted_store, first, "0.04", usage=Usage(400000, 0, 0))
    fresh = authorize_native_user({**claims, "nonce": "fresh"}, cfg, time.time())
    hosted_store.register_login(fresh)
    second = hosted_store.provision(fresh, tasks_per_hour=5)
    with pytest.raises(ProviderError):
        settle(hosted_store, second, "0.02", usage=Usage(200000, 0, 0))
    other = authorize_native_user({**claims, "sub": "fixture-B", "nonce": "B"}, cfg, time.time())
    hosted_store.register_login(other)
    token = hosted_store.provision(other, tasks_per_hour=5)
    with pytest.raises(ProviderError):
        settle(hosted_store, token, "0.02", usage=Usage(200000, 0, 0))


def test_eight_requests_and_task_budget_are_independently_enforced(hosted_store, enabled, login):
    token = hosted_store.provision(login, tasks_per_hour=5)
    for _ in range(8):
        settle(hosted_store, token, "0.001", usage=Usage(100, 20, 0))
    with pytest.raises(ProviderError):
        settle(hosted_store, token, "0.001", usage=Usage(100, 20, 0))
    token = hosted_store.provision(login, tasks_per_hour=5)
    with pytest.raises(ProviderError):
        settle(hosted_store, token, "0.050001", usage=Usage(1, 0, 0))


@pytest.mark.parametrize("state", ["unknown", "reserved", "oversized"])
def test_ambiguous_or_unsafe_usage_blocks_after_restart_and_purge(
    hosted_store, enabled, login, state
):
    token = hosted_store.provision(login, tasks_per_hour=5)
    price = Pricing.load("config/model_pricing.json", "gpt-6-luna")
    spend = Spending(hosted_store, token)
    ident = spend.reserve(Decimal("0.001"), price, "fixture")
    if state != "reserved":
        spend.reconcile(
            ident,
            price,
            None if state == "unknown" else Usage(900000, 0, 0),
            bound=20000,
            output_limit=512,
        )
    with pytest.raises(SafeError):
        hosted_store.set_kill(enabled=True)
    hosted_store.purge_content(before=time.time() + 1)
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "OPENAI_API_KEY",
            "LLM_API_KEY",
            "OIDC_CLIENT_SECRET",
            "HOSTED_COOKIE_SECRET",
            "HOSTED_PRINCIPAL_SECRET",
            "HOSTED_REVIEWERS_JSON",
        }
    }
    env["CASE_DB"] = str(hosted_store.db.path)
    script = """
import os
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database
s=HostedStore(Database(os.environ['CASE_DB']))
with s.db.connect() as c:
 r=c.execute('SELECT * FROM hosted_calls').fetchone()
 assert r is not None and r['reserved']=='0.001'
 assert c.execute('SELECT count(*) FROM tasks').fetchone()[0]==1
 assert c.execute('SELECT count(*) FROM cost_records').fetchone()[0]==0
 assert r['status'] in ('reserved','unknown','recorded')
 if r['status']!='recorded': assert r['cost'] is None
 assert not s.operations_allowed(c) or r['status']=='reserved'
print('PERSISTED')
"""
    out = subprocess.check_output([sys.executable, "-c", script], env=env, text=True, timeout=20)
    assert out.strip() == "PERSISTED"
    assert not Spending.available(hosted_store, login)


def test_single_operation_is_exclusive_across_processes(hosted_settings):
    path = hosted_settings.data_dir / "agent.active.lock"
    with single_operation(path):
        script = """
from pathlib import Path
import sys
from yemen_customer_service.hosting.spending import single_operation
from yemen_customer_service.agent.provider import ProviderError
try:
 with single_operation(Path(sys.argv[1])): raise AssertionError('Concurrent operation allowed')
except ProviderError: print('BUSY')
"""
        assert (
            subprocess.check_output(
                [sys.executable, "-c", script, str(path)], text=True, timeout=20
            ).strip()
            == "BUSY"
        )


def test_expired_approval_and_kill_block_before_new_reservation(hosted_store, enabled, login):
    token = hosted_store.provision(login, tasks_per_hour=5)
    hosted_store.set_kill(enabled=False)
    with pytest.raises(ProviderError):
        settle(hosted_store, token, "0.001", usage=Usage(1, 1, 0))
    hosted_store.set_kill(enabled=True)
    with hosted_store.db.connect(write=True) as c:
        c.execute("UPDATE hosted_control SET approval_until=0")
    with pytest.raises(ProviderError):
        settle(hosted_store, token, "0.001", usage=Usage(1, 1, 0))
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 0


def test_hosted_memory_scope_and_capability_survive_real_process_restart(
    hosted_store, hosted_settings, claims, login
):
    token = hosted_store.provision(login, tasks_per_hour=5)
    hosted_store.remember(token, "Synthetic favorite colour is teal.")
    other = authorize_native_user(
        {**claims, "sub": "fixture-B", "nonce": "scope-B"}, hosted_settings, time.time()
    )
    hosted_store.register_login(other)
    foreign = hosted_store.provision(other, tasks_per_hour=5)
    assert hosted_store.recall(foreign) == []
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "OPENAI_API_KEY",
            "LLM_API_KEY",
            "OIDC_CLIENT_SECRET",
            "HOSTED_COOKIE_SECRET",
            "HOSTED_PRINCIPAL_SECRET",
            "HOSTED_REVIEWERS_JSON",
        }
    }
    env.update(CASE_DB=str(hosted_store.db.path), CASE_TOKEN=token)
    script = """
import os
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database
store=HostedStore(Database(os.environ['CASE_DB']))
assert store.recall(os.environ['CASE_TOKEN'])==['Synthetic favorite colour is teal.']
print('RECALLED')
"""
    assert (
        subprocess.check_output(
            [sys.executable, "-c", script], env=env, text=True, timeout=20
        ).strip()
        == "RECALLED"
    )
