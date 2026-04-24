import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.repositories.sqlite_adapter import engine
from app.models.user import User
from app.models.expense import ExpenseCreate, ExpenseCategory
from app.services.expense_service import ExpenseService
from app.models.mileage import MileageLogCreate
from app.services.mileage_service import MileageService
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.contact import Contact


def resolve_import_dir() -> Path:
    candidates = [
        Path("tmp/import_data"),
        Path(__file__).resolve().parents[2] / "tmp/import_data",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def parse_date(value: str):
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    raise ValueError(f"Unrecognized date format: {value}")


def parse_date_only(value: str):
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue
    raise ValueError(f"Unrecognized date format: {value}")


def to_float(x: Optional[str]) -> float:
    x = (x or "").replace(",", "").strip()
    try:
        return float(x) if x else 0.0
    except Exception:
        return 0.0


def none_if_null(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    s = x.strip()
    return None if s.upper() == "NULL" or s == "" else s


def import_expenses(session: Session, user: User, import_dir: Path) -> dict:
    category_map = {
        "ingredients": ExpenseCategory.INGREDIENTS,
        "supplies": ExpenseCategory.SUPPLIES,
        "box": ExpenseCategory.SUPPLIES,
        "board": ExpenseCategory.SUPPLIES,
        "internet": ExpenseCategory.UTILITIES,
        "website": ExpenseCategory.MARKETING,
        "printing": ExpenseCategory.MARKETING,
        "advertising": ExpenseCategory.MARKETING,
        "memberships": ExpenseCategory.OTHER,
        "courses": ExpenseCategory.OTHER,
        "travel": ExpenseCategory.OTHER,
        "fees": ExpenseCategory.FEES,
        "utilities": ExpenseCategory.UTILITIES,
        "rent": ExpenseCategory.RENT,
        "marketing": ExpenseCategory.MARKETING,
        "other": ExpenseCategory.OTHER,
    }
    matches = list(import_dir.glob("*Expenses*.csv"))
    exp_service = ExpenseService(session=session)
    imported = skipped = 0
    errors = []
    for file_path in matches:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                try:
                    date_val = parse_date_only(row.get("ExpenseDate", ""))
                    description = (row.get("Description") or "").strip() or "(no description)"
                    vendor = (row.get("Vendor") or "").strip() or None
                    amount = to_float(row.get("Amount"))
                    vat_amount = to_float(row.get("VatAmount"))
                    category_raw = (row.get("Category") or "").strip().lower()
                    category = category_map.get(category_raw, ExpenseCategory.OTHER)
                    payment_source = (row.get("PaymentSource") or "").strip() or None
                    exp_in = ExpenseCreate(
                        user_id=user.id,
                        date=date_val,
                        description=description,
                        amount=amount,
                        category=category,
                        vat_amount=vat_amount,
                        payment_source=payment_source,
                        vendor=vendor,
                    )
                    # service will persist
                    import asyncio

                    asyncio.get_event_loop().run_until_complete(
                        exp_service.create_expense(expense_in=exp_in, current_user=user)
                    )
                    imported += 1
                except Exception as e:
                    skipped += 1
                    errors.append(f"{file_path.name} line {idx}: {e}")
    return {"imported": imported, "skipped": skipped, "errors": errors}


def import_mileage(session: Session, user: User, import_dir: Path) -> dict:
    matches = list(import_dir.glob("*Mileage*.csv"))
    mil_service = MileageService(session=session)
    imported = skipped = 0
    errors = []
    for file_path in matches:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                try:
                    date_val = parse_date_only(row.get("Date", ""))
                    purpose = (row.get("Purpose") or "").strip() or None
                    distance = to_float(row.get("Miles") or row.get("Distance"))
                    order_ref = (row.get("OrderRef") or "").strip() or None
                    notes = (row.get("Description") or "").strip() or None
                    log_in = MileageLogCreate(
                        user_id=user.id,
                        date=date_val,
                        distance=distance,
                        purpose=purpose,
                        order_ref=order_ref,
                        notes=notes,
                    )
                    import asyncio

                    asyncio.get_event_loop().run_until_complete(
                        mil_service.create_mileage_log(log_in=log_in, current_user=user)
                    )
                    imported += 1
                except Exception as e:
                    skipped += 1
                    errors.append(f"{file_path.name} line {idx}: {e}")
    return {"imported": imported, "skipped": skipped, "errors": errors}


def status_from_row(row: dict) -> OrderStatus:
    is_quote = (row.get("IsQuote") or "0").strip()
    if is_quote in ("1", "true", "True"):
        return OrderStatus.INQUIRY
    status_raw = (row.get("OrderStatusId") or "").strip()
    if status_raw == "2":
        return OrderStatus.CONFIRMED
    if status_raw == "3":
        return OrderStatus.IN_PROGRESS
    if status_raw == "4":
        return OrderStatus.COMPLETED
    if status_raw == "5":
        return OrderStatus.CANCELLED
    return OrderStatus.INQUIRY


def import_orders(session: Session, user: User, import_dir: Path) -> dict:
    matches = list(import_dir.glob("*Orders*.csv"))
    imported = skipped = 0
    errors = []
    for file_path in matches:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                try:
                    if (row.get("IsQuote") or "0").strip() in ("1", "true", "True"):
                        skipped += 1
                        continue
                    order_number = (row.get("OrderNumber") or "").strip()
                    if not order_number:
                        skipped += 1
                        errors.append(f"{file_path.name} line {idx}: Missing OrderNumber")
                        continue
                    # dedupe
                    stmt = select(Order).where(
                        Order.order_number == order_number, Order.user_id == user.id
                    )
                    if session.exec(stmt).first():
                        skipped += 1
                        continue

                    order_date = parse_date(row.get("OrderDate", ""))
                    if order_date.tzinfo is None:
                        order_date = order_date.replace(tzinfo=timezone.utc)
                    due_date = order_date

                    subtotal = to_float(row.get("SubTotalAmount"))
                    discount = to_float(row.get("DiscountAmount"))
                    total = to_float(row.get("TotalAmount"))
                    delivery_fee = to_float(row.get("SetupDeliveryAmount"))
                    tax = (
                        to_float(row.get("ShippingTaxAmount"))
                        + to_float(row.get("TaxAmount1"))
                        + to_float(row.get("TaxAmount2"))
                        + to_float(row.get("TaxAmount3"))
                        + to_float(row.get("TaxAmount4"))
                        + to_float(row.get("TaxAmount5"))
                    )
                    # contact
                    contact_name = none_if_null(row.get("Contact"))
                    contact_email = none_if_null(row.get("ContactEmail"))
                    contact_company = none_if_null(row.get("ContactCompany"))
                    existing_contact = None
                    if contact_email:
                        stmt_c = select(Contact).where(
                            Contact.user_id == user.id, Contact.email == contact_email
                        )
                        existing_contact = session.exec(stmt_c).first()
                    if existing_contact is None and contact_name:
                        parts = contact_name.split()
                        first = parts[0] if parts else None
                        last = " ".join(parts[1:]) if len(parts) > 1 else None
                        stmt_c2 = select(Contact).where(
                            Contact.user_id == user.id,
                            Contact.first_name == first,
                            Contact.last_name == last,
                            Contact.company_name == contact_company,
                        )
                        existing_contact = session.exec(stmt_c2).first()
                    customer_id = None
                    if existing_contact is None and (contact_name or contact_email or contact_company):
                        parts = (contact_name or "").split()
                        first = parts[0] if parts else None
                        last = " ".join(parts[1:]) if len(parts) > 1 else None
                        new_contact = Contact(
                            user_id=user.id,
                            first_name=first,
                            last_name=last,
                            company_name=contact_company,
                            email=contact_email,
                        )
                        session.add(new_contact)
                        session.commit()
                        session.refresh(new_contact)
                        customer_id = new_contact.id
                    elif existing_contact is not None:
                        customer_id = existing_contact.id

                    db_order = Order(
                        user_id=user.id,
                        order_number=order_number,
                        customer_id=customer_id,
                        customer_name=contact_name,
                        customer_company=contact_company,
                        customer_email=contact_email,
                        status=status_from_row(row),
                        payment_status=PaymentStatus.UNPAID,
                        order_date=order_date,
                        due_date=due_date,
                        delivery_fee=delivery_fee or 0,
                        subtotal=subtotal,
                        tax=tax,
                        discount_amount=discount or 0,
                        total_amount=total or max(0.0, subtotal + tax - discount),
                        event_type=(row.get("EventType") or None),
                        theme_details=(row.get("ThemeDetails") or None),
                        internal_notes=(row.get("Notes") or None),
                    )
                    session.add(db_order)
                    session.commit()
                    session.refresh(db_order)
                    imported += 1
                except Exception as e:
                    session.rollback()
                    skipped += 1
                    errors.append(f"{file_path.name} line {idx}: {e}")
    return {"imported": imported, "skipped": skipped, "errors": errors}


def main():
    import_dir = resolve_import_dir()
    with Session(engine) as session:
        user = session.exec(select(User)).first()
        if not user:
            print("No user found; run seed first.")
            return
        print(f"Using user: {user.email}")
        exp = import_expenses(session, user, import_dir)
        print("Expenses:", exp)
        mil = import_mileage(session, user, import_dir)
        print("Mileage:", mil)
        ords = import_orders(session, user, import_dir)
        print("Orders:", ords)


if __name__ == "__main__":
    main()
