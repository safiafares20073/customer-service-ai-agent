"""Launcher wiring tests; actual proxy/PORT/container checks are run separately."""

import os
import subprocess
import sys

import pytest

from yemen_customer_service.hosting import launch


class CompletedChild:
    def poll(self):
        return 0

    def wait(self, **kwargs):
        return 0


@pytest.mark.parametrize("port", ["8080", "40123"])
def test_platform_port_preserves_private_worker_and_health_proxy(
    hosted_settings, monkeypatch, port
):
    monkeypatch.setattr(sys, "argv", ["hosted-launcher"])
    monkeypatch.setattr(launch, "prepare", lambda settings: settings.data_dir)
    monkeypatch.setenv("PORT", port)
    for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME"):
        monkeypatch.setenv(key, os.getenv(key, ""))
    children = []

    def spawn(command, **options):
        children.append((command, options, os.environ["PORT"]))
        return CompletedChild()

    monkeypatch.setattr(launch.subprocess, "Popen", spawn)
    previous = os.getcwd()
    previous_mask = os.umask(0o077)
    try:
        with pytest.raises(SystemExit):
            launch.main()
    finally:
        os.chdir(previous)
        os.umask(previous_mask)
    assert len(children) == 2
    assert all(c[2] == port and c[1]["start_new_session"] for c in children)
    assert children[0][0][-1] == "--worker"
    assert children[1][0] == [
        "caddy",
        "run",
        "--config",
        "/app/deployment/Caddyfile",
        "--adapter",
        "caddyfile",
    ]


@pytest.mark.parametrize("port", ["80", "8501", "65536", "invalid"])
def test_unsafe_platform_port_starts_no_child(hosted_settings, monkeypatch, port):
    monkeypatch.setattr(sys, "argv", ["hosted-launcher"])
    monkeypatch.setattr(launch, "prepare", lambda settings: settings.data_dir)
    monkeypatch.setenv("PORT", port)

    def forbidden(*args, **kwargs):
        pytest.fail("Unsafe listener must not start")

    monkeypatch.setattr(launch.subprocess, "Popen", forbidden)
    previous = os.getcwd()
    previous_mask = os.umask(0o077)
    try:
        with pytest.raises(SystemExit):
            launch.main()
    finally:
        os.chdir(previous)
        os.umask(previous_mask)


def test_resource_probe_requires_explicit_local_container_flag():
    result = subprocess.run(
        [sys.executable, "-m", "tests.hosting.railway_resource_probe"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "--run-local-containers" in result.stderr
    assert not result.stdout
