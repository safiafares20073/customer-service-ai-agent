"""Secure container startup: mounted private data, nonroot worker, loopback origin."""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database


def mounted_volume(path):
    # Linux mountinfo also recognizes bind mounts sharing the parent device.
    target = str(path.resolve())
    try:
        return any(
            line.split()[4].replace("\\040", " ") == target
            for line in Path("/proc/self/mountinfo").read_text().splitlines()
        )
    except OSError:
        return False


def validate_data_path(path):
    if not path.is_absolute() or path != Path("/var/lib/customer-service"):
        raise ValueError("Use the dedicated persistent volume")
    if any(p.is_symlink() for p in [path, *path.parents]) or not mounted_volume(path):
        raise ValueError("A real mounted persistent volume is required")
    return path


def prepare(settings):
    path = validate_data_path(settings.data_dir)
    # Entrypoint starts as root only to assign the dedicated volume, then drops permanently.
    if os.geteuid() == 0:
        os.chown(path, 10001, 10001)
        os.chmod(path, 0o700)
        os.setgroups([])
        os.setgid(10001)
        os.setuid(10001)
    if os.geteuid() == 0 or path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o077:
        raise ValueError("Private nonroot volume access is required")
    for item in path.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlinks in runtime data are forbidden")
    store = HostedStore(Database(path / "customer_service.sqlite3"))
    store.initialize_hosted()  # Refuses development or fixture data; does not seed orders/users.
    store.configure(settings)  # Preserves kill state and lifetime accounting.
    store.purge_content()
    runtime = path / "runtime"
    secrets_dir = runtime / ".streamlit"
    secrets_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    auth = {
        "redirect_uri": settings.origin + "/oauth2callback",
        "cookie_secret": settings.cookie_secret,
    }
    lines = [
        "[auth]",
        *(f"{k} = {json.dumps(v)}" for k, v in auth.items()),
        "[auth.reviewer]",
        f"client_id = {json.dumps(settings.client_id)}",
        f"client_secret = {json.dumps(settings.client_secret)}",
        f"server_metadata_url = {json.dumps(settings.metadata_url)}",
        "[auth.reviewer.client_kwargs]",
        'scope = "openid email"' if settings.email_invites else 'scope = "openid"',
        'code_challenge_method = "S256"',
        "[auth.reviewer.authorize_params]",
        'max_age = "900"',
    ]
    # This runtime configuration is private, not a submission/evidence artifact.
    secret_file = secrets_dir / "secrets.toml"
    fd = os.open(secret_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    return runtime


def worker():
    logging.disable(logging.CRITICAL)  # SDK/Authlib exceptions must not print identities/tokens.
    os.environ.pop("OPENAI_LOG", None)
    from streamlit.web import cli

    settings = Settings.load()
    app = Path(__file__).resolve().parents[1] / "ui" / "hosted_app.py"
    sys.argv = [
        "streamlit",
        "run",
        str(app),
        "--theme.base=dark",
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--server.headless=true",
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=true",
        "--server.enableStaticServing=false",
        "--browser.gatherUsageStats=false",
        "--client.showErrorDetails=none",
        "--server.fileWatcherType=none",
        "--server.maxMessageSize=1",
        "--server.maxUploadSize=1",
        "--logger.level=error",
        f"--secrets.files={settings.data_dir / 'runtime/.streamlit/secrets.toml'}",
        f"--browser.serverAddress={urlsplit(settings.origin).hostname}",
        "--browser.serverPort=443",
    ]
    raise SystemExit(cli.main())


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        worker()
        return
    children = []
    try:
        os.umask(0o077)
        settings = Settings.load()
        runtime = prepare(settings)
        os.chdir(runtime)
        port = int(os.getenv("PORT", "10000"))
        if not 1024 <= port <= 65535 or port == 8501:
            raise ValueError("Invalid public proxy port")
        os.environ["PORT"] = str(port)
        os.environ["XDG_DATA_HOME"] = str(runtime)
        os.environ["XDG_CONFIG_HOME"] = str(runtime)
        for command in [
            [sys.executable, "-m", "yemen_customer_service.hosting.launch", "--worker"],
            ["caddy", "run", "--config", "/app/deployment/Caddyfile", "--adapter", "caddyfile"],
        ]:
            children.append(subprocess.Popen(command, start_new_session=True))

        def stop(*_):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop)
        while all(p.poll() is None for p in children):
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    except Exception:
        print("HOSTED_STARTUP_REFUSED", file=sys.stderr)
    finally:
        for process in children:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
