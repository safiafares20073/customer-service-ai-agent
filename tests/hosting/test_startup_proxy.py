import os
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
from starlette.requests import Request
from starlette.responses import Response
from streamlit.web.server.starlette import starlette_auth_routes as native_auth

from yemen_customer_service.hosting import launch


def test_startup_refuses_ephemeral_or_symlink_storage(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        launch.validate_data_path(tmp_path)
    monkeypatch.setattr(launch, "mounted_volume", lambda path: False)
    with pytest.raises(ValueError):
        launch.validate_data_path(Path("/var/lib/customer-service"))


def test_private_secret_configuration_without_root_or_network(hosted_settings, monkeypatch):
    monkeypatch.setattr(launch, "validate_data_path", lambda path: path)
    monkeypatch.setattr(launch.os, "geteuid", lambda: hosted_settings.data_dir.stat().st_uid)
    # Tests run nonroot in the workspace; production requires uid != 0.
    assert hosted_settings.data_dir.stat().st_uid != 0
    runtime = launch.prepare(hosted_settings)
    secret = runtime / ".streamlit/secrets.toml"
    assert secret.stat().st_mode & 0o777 == 0o600
    import tomllib

    cfg = tomllib.loads(secret.read_text())
    assert cfg["auth"]["redirect_uri"] == hosted_settings.origin + "/oauth2callback"
    assert cfg["auth"]["reviewer"]["client_kwargs"]["scope"] == "openid"
    assert cfg["auth"]["reviewer"]["client_kwargs"]["code_challenge_method"] == "S256"
    assert "expose_tokens" not in cfg["auth"]


def test_container_context_excludes_private_artifacts_and_paid_defaults():
    dockerignore = Path(".dockerignore").read_text()
    assert dockerignore.startswith("**\n")
    assert (
        "!artifacts" not in dockerignore
        and "!data" not in dockerignore
        and "!traces" not in dockerignore
    )
    config = Path("render.yaml").read_text()
    assert "numInstances: 1" in config and "autoDeployTrigger: off" in config
    assert "mountPath: /var/lib/customer-service" in config
    assert 'key: HOSTED_PAID_ENABLED\n        value: "false"' in config
    assert 'key: HOSTED_REVIEWERS_JSON\n        value: "[]"' in config
    assert "healthCheckPath: /healthz" in config


def test_native_identity_cookie_tampering_is_rejected(monkeypatch):
    monkeypatch.setattr(
        native_auth, "get_cookie_secret", lambda: "offline-fixture-cookie-secret" * 3
    )
    signed = native_auth._create_signed_value_wrapper(
        "_streamlit_user", '{"sub":"fixture-A"}'
    ).decode()

    def request(value):
        return Request(
            {"type": "http", "headers": [(b"cookie", ("_streamlit_user=" + value).encode())]}
        )

    assert (
        native_auth._get_signed_cookie_from_request(request(signed), "_streamlit_user")
        == b'{"sub":"fixture-A"}'
    )
    tampered = signed[:-4] + "AAAA"
    assert native_auth._get_signed_cookie_from_request(request(tampered), "_streamlit_user") is None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_actual_caddy_cookie_hardening_and_health_route(tmp_path, monkeypatch):
    # Require a real Caddy binary (image extraction documented); do not simulate a pass.
    binary = Path(os.getenv("CADDY_TEST_BINARY", "/tmp/hosting-caddy"))
    assert binary.is_file(), "Real Caddy verification binary is required"
    monkeypatch.setattr(
        native_auth, "get_cookie_secret", lambda: "offline-fixture-cookie-secret" * 3
    )
    response = Response()
    native_auth._set_single_cookie(response, "_streamlit_user", "offline-fixture")
    native_cookie = response.headers["set-cookie"]
    assert "httponly" in native_cookie.lower()

    class Upstream(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            if self.path != "/_stcore/health":
                self.send_header("Set-Cookie", native_cookie)
            self.end_headers()
            self.wfile.write(b"ok" if self.path == "/_stcore/health" else b"fixture")

        def log_message(self, *args):
            pass

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    port = free_port()
    config = (
        Path("deployment/Caddyfile")
        .read_text()
        .replace(":{$PORT}", f"http://127.0.0.1:{port}")
        .replace("127.0.0.1:8501", f"127.0.0.1:{upstream.server_port}")
    )
    path = tmp_path / "Caddyfile"
    path.write_text(config)
    process = subprocess.Popen(
        [str(binary), "run", "--config", str(path), "--adapter", "caddyfile"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            try:
                with httpx.Client(trust_env=False) as client:
                    r = client.get(f"http://127.0.0.1:{port}/", timeout=1)
                break
            except httpx.ConnectError:
                time.sleep(0.05)
        else:
            pytest.fail("Caddy did not start")
        assert r.status_code == 200
        cookie = r.headers["set-cookie"].lower()
        assert "; secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert "max-age=31536000" in r.headers["strict-transport-security"]
        with httpx.Client(trust_env=False) as client:
            health = client.get(f"http://127.0.0.1:{port}/healthz")
        assert health.status_code == 200 and health.text == "ok"
    finally:
        process.terminate()
        process.wait(timeout=10)
        upstream.shutdown()
        upstream.server_close()
