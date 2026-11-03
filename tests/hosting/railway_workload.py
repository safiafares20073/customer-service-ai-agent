"""Offline resource probe workload, never imported by the application.

An explicitly scripted official-SDK HTTP provider and real production-mode MCP
exercise read, memory and exact confirmation paths. No real IdP/OpenAI calls.
Use only a disposable local container/volume, never a deployed service.
"""

import json
import time
from dataclasses import replace
from decimal import Decimal

from tests.agent_support import SDKScript, completion
from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.controller import HostedController
from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database


def main():
    base = Settings.load()
    # Render both real UI language paths in the same constrained container.
    # This is AppTest with an anonymous user, not a live OIDC/browser claim.
    from pathlib import Path

    from streamlit import config
    from streamlit.testing.v1 import AppTest

    from yemen_customer_service.ui import chat

    config.set_option("server.address", "127.0.0.1")
    config.set_option("secrets.files", [str(base.data_dir / "runtime/.streamlit/secrets.toml")])
    app = AppTest.from_file(
        Path(chat.__file__).with_name("hosted_app.py"), default_timeout=20
    ).run()
    assert not app.exception and not app.chat_input
    app.radio[0].set_value("العربية").run()
    assert not app.exception and not app.chat_input
    assert any("direction:rtl" in e.proto.body for e in app.get("html"))
    # Separate fixture database: never promote to or alter the actual hosted DB.
    cfg = replace(
        base,
        data_dir=base.data_dir / "offline-resource-fixture",
        invites=((base.issuer, "offline-resource-subject"),),
        paid_enabled=True,
        global_budget=Decimal("1"),
        principal_budget=Decimal("0.1"),
        approval_until=time.time() + 300,
    )
    store = HostedStore(Database(cfg.data_dir / "fixture.sqlite3"))
    store.initialize_hosted(evidence_mode="fixture")
    store.configure(cfg)
    claims = {
        "is_logged_in": True,
        "iss": cfg.issuer,
        "sub": "offline-resource-subject",
        "aud": cfg.client_id,
        "iat": int(time.time()) - 1,
        "exp": int(time.time()) + 300,
        "nonce": "offline-resource-nonce",
    }
    login = authorize_native_user(claims, cfg, time.time())
    store.set_kill(enabled=True)
    scripts = []
    batches = [
        [
            completion(calls=[("search_products", {"query": "headphones"})]),
            completion(calls=[("get_store_policies", {"topic": "returns"})]),
            completion("Synthetic fixture: headphones cost $25; returns within 14 days."),
        ],
        [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Offline resource fixture",
                            "message": "Synthetic-only fixture question",
                            "idempotency_key": "offline-resource-ticket",
                        },
                    )
                ]
            )
        ],
        [completion("Synthetic fixture: the confirmed support ticket was created.")],
    ]

    def factory():
        script = SDKScript(batches.pop(0))
        scripts.append(script)
        return script.provider

    controller = HostedController(store, login, cfg, provider_factory=factory)
    controller.submit("Find headphones under $30 and explain returns", "probe-read", "en")
    assert controller.status == "completed", controller.error
    controller.submit("افتح تذكرة دعم مصطنعة", "probe-ticket", "ar")
    assert controller.draft is not None and not controller.error
    controller.decide(confirm=True, revision=controller.revision, locale="ar")
    assert controller.status == "completed" and controller.draft is None
    with store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM memory").fetchone()[0] > 0
        calls = c.execute("SELECT provider,status FROM hosted_calls").fetchall()
        assert len(calls) == 5 and all(tuple(r) == ("fixture", "recorded") for r in calls)
        allowed = {r[0] for r in c.execute("SELECT tool FROM audits WHERE outcome='allow'")}
        assert {"search_products", "get_store_policies", "create_support_ticket"} <= allowed
        assert not c.execute(
            "SELECT 1 FROM audits WHERE tool!='agent' AND outcome IN ('deny','error')"
        ).fetchone()
        # A safe confirmation pause is deliberately audited as a denial.
        assert (
            c.execute(
                "SELECT count(*) FROM audits WHERE tool='agent' AND outcome='deny' "
                "AND result_code='AWAITING_CONFIRMATION'"
            ).fetchone()[0]
            == 1
        )
    assert not batches and all(not s.actions for s in scripts)
    # Leave a real MCP subprocess initialized long enough for external sampling.
    import asyncio

    from yemen_customer_service.tool_server.client import connect

    async def sample():
        token = store.provision(login, tasks_per_hour=5)
        async with connect(store.db.path, store, token, enable_hosted_auth=True) as client:
            assert len(await client.tools_for_model()) == 7
            await asyncio.sleep(2)

    asyncio.run(sample())
    print(
        json.dumps(
            {
                "outcome": "PASS",
                "provenance": "SDK provider fixture + genuine MCP",
                "fixture_requests": 5,
                "paid_requests": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
