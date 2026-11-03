from datetime import date

import pytest

from tests.agent_support import MODEL, SDKScript
from yemen_customer_service.agent.pricing import Pricing


@pytest.fixture
def pricing():
    return Pricing.load("config/model_pricing.json", MODEL, today=date(2026, 11, 3))


@pytest.fixture
async def sdk_script():
    scripts = []

    def factory(actions):
        script = SDKScript(actions)
        scripts.append(script)
        return script

    yield factory
    for script in scripts:
        await script.close()
