"""Create or reload the SQLite repair-cost database.

    python -m app.seed            create tables and load prices if empty
    python -m app.seed --reset    replace prices and sources with seed_data.py
    python -m app.seed --show     print the price table
"""

from __future__ import annotations

import argparse

from .config import get_settings
from .database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="reload prices and sources from seed_data.py")
    parser.add_argument("--show", action="store_true", help="print the repair-cost table")
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.db_path)
    if args.reset:
        db.seed(reset=True)
    else:
        db.init()
    methods = db.repair_methods()
    print(f"{settings.db_path}: {len(methods)} repair methods, {len(db.sources())} sources")

    if args.show:
        for m in methods:
            top = f"{m['max_gbp']:,.0f}{'+' if m['max_open'] else ''}"
            print(
                f"  {m['damage_type']:<14} {m['method']:<55} "
                f"£{m['min_gbp']:,.0f}-£{top:<7} per {m['unit']:<10} {m['source']['publisher']}"
            )


if __name__ == "__main__":
    main()
