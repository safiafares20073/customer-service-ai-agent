from pathlib import Path

import pytest
from streamlit import config
from streamlit.testing.v1 import AppTest


@pytest.fixture
def ui_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "ui.sqlite3"))
    monkeypatch.setenv("ENABLE_DEMO_AUTH", "true")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("UI_CUSTOMER_ID", "demo-a")
    monkeypatch.setenv("UI_PROVIDER", "fixture")
    previous = config.get_option("server.address")
    config.set_option("server.address", "127.0.0.1")
    yield tmp_path
    config.set_option("server.address", previous)


@pytest.fixture
def app(ui_environment):
    return AppTest.from_file(
        Path("src/yemen_customer_service/ui/app.py").resolve(),
        default_timeout=20,
    ).run()
