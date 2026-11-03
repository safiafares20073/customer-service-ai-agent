"""Private operator controls. No HTTP admin route, identities or paid API calls."""

import argparse

from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["disable", "enable", "purge"])
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    try:
        settings = Settings.load()
        store = HostedStore(Database(settings.data_dir / "customer_service.sqlite3"))
        if args.action == "enable":
            if not args.allow_paid or not settings.paid_enabled:
                raise ValueError("Separate paid authorization required")
            store.set_kill(enabled=True)
        elif args.action == "disable":
            store.set_kill(enabled=False)
        else:
            store.purge_content()
        print("HOSTED_CONTROL_OK")
    except Exception:
        print("HOSTED_CONTROL_REFUSED")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
