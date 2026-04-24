from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import SQLModel, Session, select

from app.models import __all__ as _models  # noqa: F401
from app.models.user import User
from app.repositories.sqlite_adapter import engine, ensure_sqlite_order_schema
from app.services.marvelous_importer import MarvelousCreationsImporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Marvelous Creations XLSX data into BakeMate.")
    parser.add_argument("workbook", help="Path to the Marvelous Creations XLSX workbook")
    parser.add_argument("--user-email", required=True, help="BakeMate user email that should own imported records")
    args = parser.parse_args()

    workbook_path = Path(args.workbook).expanduser().resolve()
    if not workbook_path.exists():
        raise SystemExit(f"Workbook not found: {workbook_path}")

    SQLModel.metadata.create_all(engine)
    ensure_sqlite_order_schema(engine)

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == args.user_email)).first()
        if user is None:
            raise SystemExit(f"No BakeMate user found for email: {args.user_email}")

        importer = MarvelousCreationsImporter(session=session, current_user=user)
        result = importer.import_workbook(workbook_path)

    print("Marvelous Creations import complete")
    print(f"  contacts_created: {result.counts.contacts_created}")
    print(f"  contacts_matched: {result.counts.contacts_matched}")
    print(f"  orders_created: {result.counts.orders_created}")
    print(f"  orders_skipped_as_quotes: {result.counts.orders_skipped_as_quotes}")
    print(f"  expenses_created: {result.counts.expenses_created}")
    print(f"  mileage_created: {result.counts.mileage_created}")
    print(f"  skipped_empty_rows: {result.counts.skipped_empty_rows}")
    if result.warnings.items:
        print("Warnings:")
        for warning in result.warnings.items:
            print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
