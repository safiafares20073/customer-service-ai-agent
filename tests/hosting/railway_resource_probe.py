"""Explicitly gated LOCAL Docker profiling; never provisions Railway or calls OpenAI.

Runs the existing production image plus a separate SDK-fixture/MCP workload.
Retains unique reports, stopped containers and private volumes, even on failure.
"""

import argparse
import json
import os
import socket
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

DOCKER = [
    "env",
    "-u",
    "DOCKER_HOST",
    "-u",
    "DOCKER_CONTEXT",
    "-u",
    "DOCKER_TLS",
    "-u",
    "DOCKER_TLS_VERIFY",
    "-u",
    "DOCKER_CERT_PATH",
    "docker",
    "--host=unix:///var/run/docker.sock",
]
LIMIT = 500_000_000  # Conservative decimal interpretation of Railway's 0.5 GB.


def docker(*args):
    return subprocess.check_output([*DOCKER, *args], stderr=subprocess.STDOUT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local-containers", action="store_true", required=True)
    parser.add_argument("--image", default="customer-service-railway:review")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root.parent)  # repository root
    evidence = Path("artifacts/railway-preparation")
    evidence.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = "railway-offline-" + uuid.uuid4().hex[:12]
    inputs = evidence / (name + "-inputs")
    inputs.mkdir(mode=0o755)
    (inputs / "hosting").mkdir(mode=0o755)
    # Only copied public fixture source is readable by the container's UID.
    # Explicit chmod is needed when the caller's umask is 077.
    inputs.chmod(0o755)
    (inputs / "hosting").chmod(0o755)
    for source in ["__init__.py", "agent_support.py", "hosting/railway_workload.py"]:
        target = inputs / source
        target.write_bytes((root / source).read_bytes())
        target.chmod(0o644)
    env_file = evidence / (name + ".env")
    report_file = evidence / (name + ".json")
    values = {
        "APP_ENV": "production",
        "ENABLE_DEMO_AUTH": "false",
        "UI_PROVIDER": "openai",
        "HOSTED_DATA_DIR": "/var/lib/customer-service",
        "HOSTED_ORIGIN": "https://review.example.invalid",
        "OIDC_ISSUER": "https://oidc.example.invalid",
        "OIDC_METADATA_URL": "https://oidc.example.invalid/.well-known/openid-configuration",
        "OIDC_CLIENT_ID": "offline-fixture-client",
        "OIDC_CLIENT_SECRET": "offline-fixture-client-secret-not-a-credential",
        "HOSTED_COOKIE_SECRET": "offline-fixture-cookie-" + "x" * 50,
        "HOSTED_PRINCIPAL_SECRET": "offline-fixture-principal-" + "y" * 50,
        "HOSTED_REVIEWERS_JSON": "[]",
        "HOSTED_PAID_ENABLED": "false",
        "HOSTED_GLOBAL_BUDGET_USD": "0",
        "HOSTED_PRINCIPAL_BUDGET_USD": "0",
        "HOSTED_APPROVAL_UNTIL": "0",
        "OPENAI_MODEL": "gpt-6-luna",
        "MODEL_PRICING_FILE": "/app/config/model_pricing.json",
        "PORT": "8080",
    }
    with env_file.open("x") as f:
        env_file.chmod(0o600)
        f.write("".join(k + "=" + v + "\n" for k, v in values.items()))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    report = {
        "provenance": "LOCAL Docker, SDK provider fixture + real MCP, no live IdP/model",
        "memory_cap_bytes": LIMIT,
        "cpu_cap": 1,
        "status": "FAIL",
    }
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def ready():
        for _ in range(120):
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/healthz", headers={"Host": "healthcheck.railway.app"}
                )
                with opener.open(req, timeout=1) as r:
                    if r.status == 200 and r.read() == b"ok":
                        return
            except OSError:
                pass
            time.sleep(0.25)
        raise RuntimeError("Local health check failed")

    def execute(code):
        return docker("exec", "--user", "10001", name, "/app/.venv/bin/python", "-c", code)

    def metrics():
        code = (
            "import json,pathlib; p=pathlib.Path('/sys/fs/cgroup'); "
            "read=lambda n:(p/n).read_text().strip(); "
            "print(json.dumps({n:read(n) for n in "
            "['memory.current','memory.peak','memory.max','memory.events',"
            "'memory.swap.max','cpu.max','cpu.stat']}))"
        )
        result = json.loads(execute(code))
        report.setdefault("cgroup_observations", []).append(result)
        # Linux page-aligns the cgroup byte limit; accept only rounding down.
        assert 0 <= LIMIT - int(result["memory.max"]) < 4096
        assert result["memory.swap.max"] == "0"
        assert result["cpu.max"] == "100000 100000"
        events = dict(line.split() for line in result["memory.events"].splitlines())
        assert int(events["oom_kill"]) == 0 and int(events["oom"]) == 0
        return result

    created = False
    try:
        image = json.loads(docker("image", "inspect", args.image))[0]
        report["image_id"], report["image_bytes"] = image["Id"], image["Size"]
        assert image["Size"] < 4_000_000_000
        docker("volume", "create", name + "-data")
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--memory",
            str(LIMIT),
            "--memory-swap",
            str(LIMIT),
            "--cpus",
            "1",
            "--env-file",
            str(env_file.resolve()),
            "-p",
            f"127.0.0.1:{port}:8080",
            "--mount",
            f"type=volume,src={name}-data,dst=/var/lib/customer-service",
            "--mount",
            f"type=bind,src={inputs.resolve()},dst=/opt/railway-validation/tests,readonly",
            args.image,
        )
        created = True
        ready()
        report["startup"] = metrics()
        for route in ["/", "/customer_service.sqlite3", "/.streamlit/secrets.toml"]:
            with opener.open(f"http://127.0.0.1:{port}" + route, timeout=5) as r:
                body = r.read()
                assert r.status == 200 and r.headers["X-Frame-Options"] == "DENY"
                assert r.headers["X-Content-Type-Options"] == "nosniff"
                assert not body.startswith(b"SQLite format")
                assert all(v.encode() not in body for k, v in values.items() if "SECRET" in k)
        output = docker(
            "exec",
            "--user",
            "10001",
            "-w",
            "/app",
            "-e",
            "PYTHONPATH=/opt/railway-validation",
            name,
            "/app/.venv/bin/python",
            "/opt/railway-validation/tests/hosting/railway_workload.py",
        )
        report["workload"] = json.loads(output.splitlines()[-1])
        assert report["workload"]["outcome"] == "PASS"
        report["after_workload"] = metrics()
        code = (
            "import sqlite3,pathlib; "
            "c=sqlite3.connect('/var/lib/customer-service/customer_service.sqlite3'); "
            "assert c.execute('SELECT count(*) FROM hosted_calls').fetchone()[0]==0; "
            "assert c.execute('SELECT count(*) FROM customers').fetchone()[0]==0; "
            "assert c.execute('SELECT kill,paid,blocked FROM hosted_control')"
            ".fetchone()==(1,0,0); "
            "assert pathlib.Path('/proc/1/status').read_text()"
            ".split('Uid:')[1].split()[0]=='10001'; "
            "c.execute(\"INSERT INTO metadata VALUES ('railway_offline_probe','retained')\"); "
            "c.commit(); "
            "print('PASS')"
        )
        assert execute(code) == "PASS"
        docker("restart", name)
        ready()
        assert (
            execute(
                "import sqlite3; "
                "c=sqlite3.connect('/var/lib/customer-service/customer_service.sqlite3'); "
                'assert c.execute("SELECT value FROM metadata WHERE '
                "key='railway_offline_probe'\").fetchone()[0]=='retained'; "
                "assert c.execute('SELECT kill,paid,blocked FROM hosted_control')"
                ".fetchone()==(1,0,0); "
                "assert c.execute('SELECT count(*) FROM hosted_calls').fetchone()[0]==0; "
                "print('PASS')"
            )
            == "PASS"
        )
        report["restart"] = metrics()
        info = json.loads(docker("container", "inspect", "--size", name))[0]
        report["ephemeral_writable_bytes"] = info["SizeRw"]
        assert info["SizeRw"] < 1_000_000_000
        report["private_volume_payload_bytes"] = int(
            execute(
                "import pathlib; p=pathlib.Path('/var/lib/customer-service'); "
                "print(sum(f.stat().st_size for f in p.rglob('*') if f.is_file()))"
            )
        )
        assert report["private_volume_payload_bytes"] < 500_000_000
        report["status"] = "PASS"
    except Exception as exc:
        # Controlled fixture/Docker diagnostic stays in ignored evidence, not public logs.
        report["failure_type"] = type(exc).__name__
        if isinstance(exc, subprocess.CalledProcessError):
            (evidence / (name + "-failure.log")).write_text(exc.output)
        raise
    finally:
        if created:
            try:
                (evidence / (name + "-startup.log")).write_text(docker("logs", name))
                docker("stop", name)
            except subprocess.CalledProcessError:
                pass
        with report_file.open("x") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
