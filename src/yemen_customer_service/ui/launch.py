"""Start the synthetic Streamlit UI on loopback only. No public demo login."""

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        required=True,
        help="Explicitly enable synthetic development identities",
    )
    parser.add_argument("--customer", choices=["demo-a", "demo-b"], default="demo-a")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    if os.getenv("APP_ENV", "development") != "development":
        parser.error("Synthetic UI is restricted to local development.")
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged local port.")
    if os.getenv("UI_PROVIDER", "fixture") == "openai" and not args.allow_paid:
        parser.error("OpenAI mode requires separate explicit paid-run approval.")
    os.environ["ENABLE_DEMO_AUTH"] = "true"
    os.environ["UI_CUSTOMER_ID"] = args.customer
    os.environ["UI_PAID_APPROVED"] = "true" if args.allow_paid else "false"
    os.environ.setdefault("UI_PROVIDER", "fixture")
    os.environ.pop("OPENAI_LOG", None)  # No SDK request/body/header debugging in this UI process.
    import sys

    from streamlit.web import cli

    app = Path(__file__).with_name("app.py")
    sys.argv = [
        "streamlit",
        "run",
        str(app),
        "--theme.base=dark",
        "--server.address=127.0.0.1",
        f"--server.port={args.port}",
        "--server.headless=true",
        "--server.enableXsrfProtection=true",
        "--server.enableCORS=true",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
        "--client.showErrorDetails=none",
        "--logger.level=warning",
    ]
    raise SystemExit(cli.main())
