from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys

from sqlmodel import SQLModel, Session, create_engine, select

from app.models.contact import Contact
from app.models.expense import Expense
from app.models.mileage import MileageLog
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.user import User
from app.services.marvelous_importer import (
    MarvelousCreationsImporter,
    coerce_bool,
    coerce_datetime,
    infer_payment_status,
    normalize_phone,
    parse_order_items,
)


def make_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_user(session: Session) -> User:
    user = User(email="importer@example.com", hashed_password="x")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_excel_serial_dates_and_phone_normalization():
    dt = coerce_datetime(45292)
    assert dt is not None
    assert dt.date() == date(2024, 1, 1)
    assert normalize_phone("1-555-123-4567") == "(555) 123-4567"


def test_coerce_bool_treats_numeric_truthy_values_as_true():
    assert coerce_bool(1) is True
    assert coerce_bool(1.0) is True
    assert coerce_bool(0) is False
    assert coerce_bool(0.0) is False


def test_parse_order_items_supports_jsonish_sources():
    items = parse_order_items(
        {
            "ProductItems": '[{"name": "Cake", "quantity": 2, "total_price": 40}]',
            "ProductRecipes": "['Buttercream']",
        },
        subtotal=60,
        total_amount=64.8,
    )
    assert len(items) == 2
    assert {item["name"] for item in items} == {"Cake", "Buttercream"}
    assert round(sum(item["total_price"] for item in items), 2) == 60.0


def test_parse_order_items_supports_legacy_product_item_keys():
    items = parse_order_items(
        {
            "ProductItems": '[{"ProductType": "Cupcake", "Quantity": 3, "SellingPrice": 4.5}]',
        },
        subtotal=13.5,
        total_amount=13.5,
    )
    assert items == [
        {
            "name": "Cupcake",
            "description": None,
            "quantity": 3,
            "unit_price": 4.5,
            "total_price": 13.5,
        }
    ]


def test_infer_payment_status_uses_explicit_balance_math_and_payment_notes():
    assert infer_payment_status(
        row={},
        total_amount=200.0,
        deposit_amount=50.0,
        amount_paid=0.0,
        balance_due=150.0,
        has_explicit_amount_paid=False,
        has_explicit_balance_due=True,
    ) == PaymentStatus.DEPOSIT_PAID

    assert infer_payment_status(
        row={"Notes": "Customer is fully paid and ready for pickup"},
        total_amount=200.0,
        deposit_amount=50.0,
        amount_paid=0.0,
        balance_due=200.0,
        has_explicit_amount_paid=False,
        has_explicit_balance_due=False,
    ) == PaymentStatus.PAID_IN_FULL

    assert infer_payment_status(
        row={"JobSheetNotes": "Deposit paid via cash app"},
        total_amount=200.0,
        deposit_amount=50.0,
        amount_paid=0.0,
        balance_due=200.0,
        has_explicit_amount_paid=False,
        has_explicit_balance_due=False,
    ) == PaymentStatus.DEPOSIT_PAID


def test_importer_imports_contacts_orders_expenses_and_mileage():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)

        result = importer.import_sheets(
            contacts_rows=[
                {
                    "ContactID": "C-1",
                    "FirstName": "Jamie",
                    "LastName": "Rivera",
                    "EmailAddress": "JAMIE@example.com",
                    "Number": "5551234567",
                    "Address": "123 Baker St\nAlbany, NY 12207",
                }
            ],
            orders_rows=[
                {
                    "OrderNumber": "MC-1001",
                    "OrderDate": 45292,
                    "DueDate": 45295,
                    "Contact": "Jamie Rivera",
                    "ContactEmail": "jamie@example.com",
                    "ContactCompany": "Marvelous Creations",
                    "Number": "5551234567",
                    "EventType": "Birthday Cake",
                    "ThemeDetails": "Blue ombre",
                    "IsQuote": 0,
                    "OrderStatusId": 7,
                    "ProductItems": '[{"ProductType": "Tiered Cake", "Quantity": 1, "SellingPrice": 100}]',
                    "ProductRecipes": '[{"name": "Buttercream", "quantity": 1, "total_price": 20}]',
                    "SubTotalAmount": 120,
                    "SetupDeliveryAmount": 5,
                    "ShippingTaxAmount": 1.1,
                    "TaxAmount1": 8.5,
                    "Total": 134.6,
                    "DepositAmount": 50,
                    "AmountPaid": 50,
                    "Notes": "Customer loves hydrangeas",
                    "JobSheetNotes": "Use gold board",
                },
                {
                    "OrderNumber": "MC-Q-1",
                    "IsQuote": 1.0,
                },
            ],
            expenses_rows=[
                {
                    "ExpenseDate": 45293,
                    "Description": "Cake flour",
                    "Amount": 42.25,
                    "Category": "Ingredients",
                    "Vendor": "Restaurant Depot",
                }
            ],
            mileage_rows=[
                {
                    "MileageDate": 45294,
                    "Distance": 12.5,
                    "Purpose": "Delivery",
                    "Rate": 0.67,
                    "StartLocation": "Bakery",
                    "EndLocation": "Client",
                }
            ],
        )

        assert result.counts.contacts_created == 1
        assert result.counts.orders_created == 1
        assert result.counts.orders_skipped_as_quotes == 1
        assert result.counts.expenses_created == 1
        assert result.counts.mileage_created == 1

        contacts = session.exec(select(Contact)).all()
        assert len(contacts) == 1
        assert contacts[0].email == "jamie@example.com"
        assert contacts[0].phone == "(555) 123-4567"

        orders = session.exec(select(Order)).all()
        assert len(orders) == 1
        order = orders[0]
        assert order.order_number == "MC-1001"
        assert order.order_date.date() == date(2024, 1, 1)
        assert order.status == OrderStatus.CONFIRMED
        assert order.payment_status == PaymentStatus.DEPOSIT_PAID
        assert order.subtotal == 120
        assert order.tax == 9.6
        assert order.total_amount == 134.6
        assert order.balance_due == 84.6
        assert "Legacy OrderStatusId: 7" in (order.internal_notes or "")
        assert "Legacy bakemate_status: confirmed" in (order.internal_notes or "")

        order_items = session.exec(select(OrderItem)).all()
        assert len(order_items) == 2
        assert round(sum(item.total_price for item in order_items), 2) == 120.0

        expenses = session.exec(select(Expense)).all()
        assert len(expenses) == 1
        assert expenses[0].date == date(2024, 1, 2)

        mileage = session.exec(select(MileageLog)).all()
        assert len(mileage) == 1
        assert mileage[0].reimbursement_amount == round(12.5 * 0.67, 2)


def test_importer_marks_paid_past_orders_completed_when_status_unknown():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1002",
                    "OrderDate": datetime(2023, 6, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2023, 6, 2, tzinfo=timezone.utc),
                    "Contact": "Paid Past Order",
                    "IsQuote": 0,
                    "Subtotal": 100,
                    "Tax": 0,
                    "Total": 100,
                    "AmountPaid": 100,
                    "OrderStatusId": None,
                }
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        order = session.exec(select(Order).where(Order.order_number == "MC-1002")).one()
        assert order.status == OrderStatus.COMPLETED
        assert order.payment_status == PaymentStatus.PAID_IN_FULL


def test_importer_uses_balance_due_clues_when_amount_paid_is_blank():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1002B",
                    "OrderDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 6, 2, tzinfo=timezone.utc),
                    "Contact": "Balance Math Order",
                    "IsQuote": 0,
                    "Subtotal": 200,
                    "Total": 200,
                    "DepositAmount": 50,
                    "BalanceDue": 150,
                    "OrderStatusId": 2.0,
                }
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        order = session.exec(select(Order).where(Order.order_number == "MC-1002B")).one()
        assert order.payment_status == PaymentStatus.DEPOSIT_PAID
        assert order.status == OrderStatus.IN_PROGRESS
        assert "Legacy DepositAmount: 50" in (order.internal_notes or "")
        assert "Legacy BalanceDue: 150" in (order.internal_notes or "")


def test_importer_maps_numeric_order_status_ids_to_bakemate_statuses():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1003",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Cancelled Order",
                    "IsQuote": 0,
                    "Subtotal": 50,
                    "Total": 50,
                    "OrderStatusId": 8,
                }
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        order = session.exec(select(Order).where(Order.order_number == "MC-1003")).one()
        assert order.status == OrderStatus.CANCELLED
        assert "Legacy OrderStatusId: 8" in (order.internal_notes or "")
        assert "Legacy bakemate_status: cancelled" in (order.internal_notes or "")


def test_importer_maps_legacy_numeric_status_2_to_confirmed_for_non_quotes():
    active_due = datetime.now(timezone.utc) - timedelta(days=364)

    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1003A",
                    "OrderDate": active_due - timedelta(days=14),
                    "DueDate": active_due,
                    "Contact": "Active Order",
                    "IsQuote": 0,
                    "Subtotal": 50,
                    "Total": 50,
                    "OrderStatusId": 2.0,
                }
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        order = session.exec(select(Order).where(Order.order_number == "MC-1003A")).one()
        assert order.status == OrderStatus.CONFIRMED
        assert order.payment_status == PaymentStatus.UNPAID
        assert "Legacy OrderStatusId: 2.0" in (order.internal_notes or "")
        assert "Legacy bakemate_status: confirmed" in (order.internal_notes or "")


def test_importer_uses_due_date_and_payment_for_legacy_numeric_statuses():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1004",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Paid Delivered Order",
                    "IsQuote": 0,
                    "Subtotal": 75,
                    "Total": 75,
                    "AmountPaid": 75,
                    "OrderStatusId": 7.0,
                },
                {
                    "OrderNumber": "MC-1005",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Unpaid Past Order",
                    "IsQuote": 0,
                    "Subtotal": 80,
                    "Total": 80,
                    "OrderStatusId": 7,
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        completed = session.exec(select(Order).where(Order.order_number == "MC-1004")).one()
        assert completed.status == OrderStatus.COMPLETED
        assert completed.payment_status == PaymentStatus.PAID_IN_FULL

        in_progress = session.exec(select(Order).where(Order.order_number == "MC-1005")).one()
        assert in_progress.status == OrderStatus.IN_PROGRESS
        assert in_progress.payment_status == PaymentStatus.UNPAID


def test_importer_refines_past_due_ambiguous_legacy_statuses_without_touching_raw_notes():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1005A",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "Contact": "Legacy Paid Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": 90,
                    "Total": 90,
                    "AmountPaid": 90,
                    "OrderStatusId": 2.0,
                },
                {
                    "OrderNumber": "MC-1005B",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "Contact": "Legacy Deposit Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": 120,
                    "Total": 120,
                    "AmountPaid": 40,
                    "OrderStatusId": 0.0,
                },
                {
                    "OrderNumber": "MC-1005C",
                    "OrderDate": datetime.now(timezone.utc),
                    "DueDate": datetime(2099, 1, 10, tzinfo=timezone.utc),
                    "Contact": "Future Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": 120,
                    "Total": 120,
                    "AmountPaid": 40,
                    "OrderStatusId": 2.0,
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )

        completed = session.exec(select(Order).where(Order.order_number == "MC-1005A")).one()
        assert completed.status == OrderStatus.COMPLETED
        assert completed.payment_status == PaymentStatus.PAID_IN_FULL
        assert "Legacy OrderStatusId: 2.0" in (completed.internal_notes or "")
        assert "Legacy legacy_status_raw: 2.0" in (completed.internal_notes or "")
        assert "Legacy bakemate_status: completed" in (completed.internal_notes or "")

        historical_in_progress = session.exec(select(Order).where(Order.order_number == "MC-1005B")).one()
        assert historical_in_progress.status == OrderStatus.IN_PROGRESS
        assert historical_in_progress.payment_status == PaymentStatus.DEPOSIT_PAID
        assert "Legacy OrderStatusId: 0.0" in (historical_in_progress.internal_notes or "")
        assert "Legacy legacy_status_raw: 0.0" in (historical_in_progress.internal_notes or "")
        assert "Legacy bakemate_status: in_progress" in (historical_in_progress.internal_notes or "")

        future_confirmed = session.exec(select(Order).where(Order.order_number == "MC-1005C")).one()
        assert future_confirmed.status == OrderStatus.CONFIRMED
        assert future_confirmed.payment_status == PaymentStatus.DEPOSIT_PAID


def test_importer_marks_very_old_ambiguous_zero_balance_legacy_rows_as_completed():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1005D",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "Contact": "Legacy Zero Total Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": 0,
                    "Total": 0,
                    "AmountPaid": 0,
                    "BalanceDue": 0,
                    "OrderStatusId": 2.0,
                },
                {
                    "OrderNumber": "MC-1005E",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "Contact": "Legacy Negative Total Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": -10,
                    "Total": -10,
                    "AmountPaid": 0,
                    "BalanceDue": -10,
                    "OrderStatusId": 0.0,
                },
                {
                    "OrderNumber": "MC-1005F",
                    "OrderDate": datetime.now(timezone.utc),
                    "DueDate": datetime.now(timezone.utc),
                    "Contact": "Recent Zero Total Ambiguous Order",
                    "IsQuote": 0,
                    "Subtotal": 0,
                    "Total": 0,
                    "AmountPaid": 0,
                    "BalanceDue": 0,
                    "OrderStatusId": 2.0,
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )

        historical_zero_total = session.exec(select(Order).where(Order.order_number == "MC-1005D")).one()
        assert historical_zero_total.status == OrderStatus.COMPLETED
        assert historical_zero_total.payment_status == PaymentStatus.UNPAID
        assert "Legacy OrderStatusId: 2.0" in (historical_zero_total.internal_notes or "")
        assert "Legacy legacy_status_raw: 2.0" in (historical_zero_total.internal_notes or "")
        assert "Legacy bakemate_status: completed" in (historical_zero_total.internal_notes or "")

        historical_negative_total = session.exec(select(Order).where(Order.order_number == "MC-1005E")).one()
        assert historical_negative_total.status == OrderStatus.COMPLETED
        assert historical_negative_total.payment_status == PaymentStatus.UNPAID
        assert "Legacy OrderStatusId: 0.0" in (historical_negative_total.internal_notes or "")
        assert "Legacy legacy_status_raw: 0.0" in (historical_negative_total.internal_notes or "")
        assert "Legacy bakemate_status: completed" in (historical_negative_total.internal_notes or "")

        recent_zero_total = session.exec(select(Order).where(Order.order_number == "MC-1005F")).one()
        assert recent_zero_total.status == OrderStatus.CONFIRMED
        assert recent_zero_total.payment_status == PaymentStatus.UNPAID


def test_importer_marks_only_ancient_ambiguous_unpaid_rows_as_completed():
    ancient_due = datetime.now(timezone.utc) - timedelta(days=731)
    newer_due = datetime.now(timezone.utc) - timedelta(days=364)

    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1005G",
                    "OrderDate": ancient_due - timedelta(days=14),
                    "DueDate": ancient_due,
                    "Contact": "Ancient Ambiguous Unpaid Order",
                    "IsQuote": 0,
                    "Subtotal": 150,
                    "Total": 150,
                    "AmountPaid": 0,
                    "BalanceDue": 150,
                    "OrderStatusId": 2.0,
                },
                {
                    "OrderNumber": "MC-1005H",
                    "OrderDate": newer_due - timedelta(days=14),
                    "DueDate": newer_due,
                    "Contact": "Not Ancient Ambiguous Unpaid Order",
                    "IsQuote": 0,
                    "Subtotal": 150,
                    "Total": 150,
                    "AmountPaid": 0,
                    "BalanceDue": 150,
                    "OrderStatusId": 0.0,
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )

        ancient_unpaid = session.exec(select(Order).where(Order.order_number == "MC-1005G")).one()
        assert ancient_unpaid.status == OrderStatus.COMPLETED
        assert ancient_unpaid.payment_status == PaymentStatus.UNPAID
        assert "Legacy OrderStatusId: 2.0" in (ancient_unpaid.internal_notes or "")
        assert "Legacy legacy_status_raw: 2.0" in (ancient_unpaid.internal_notes or "")
        assert "Legacy bakemate_status: completed" in (ancient_unpaid.internal_notes or "")

        not_ancient_unpaid = session.exec(select(Order).where(Order.order_number == "MC-1005H")).one()
        assert not_ancient_unpaid.status == OrderStatus.CONFIRMED
        assert not_ancient_unpaid.payment_status == PaymentStatus.UNPAID
        assert "Legacy OrderStatusId: 0.0" in (not_ancient_unpaid.internal_notes or "")
        assert "Legacy legacy_status_raw: 0.0" in (not_ancient_unpaid.internal_notes or "")



def test_importer_infers_delivery_method_from_delivery_fees_and_notes():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1006",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Delivery Fee Order",
                    "IsQuote": 0,
                    "Subtotal": 60,
                    "Total": 70,
                    "SetupDeliveryAmount": 10,
                },
                {
                    "OrderNumber": "MC-1007",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Pickup Note Order",
                    "IsQuote": 0,
                    "Subtotal": 40,
                    "Total": 40,
                    "Notes": "Customer requested porch pickup after 4pm",
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        delivery_order = session.exec(select(Order).where(Order.order_number == "MC-1006")).one()
        assert delivery_order.delivery_method == "delivery"

        pickup_order = session.exec(select(Order).where(Order.order_number == "MC-1007")).one()
        assert pickup_order.delivery_method == "pickup"


def test_importer_uses_payment_note_clues_when_numeric_fields_are_blank():
    with make_session() as session:
        user = make_user(session)
        importer = MarvelousCreationsImporter(session, user)
        importer.import_sheets(
            contacts_rows=[],
            orders_rows=[
                {
                    "OrderNumber": "MC-1007B",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Note Clue Order",
                    "IsQuote": 0,
                    "Subtotal": 120,
                    "Total": 120,
                    "OrderStatusId": 2.0,
                    "JobSheetNotes": "Deposit paid via Zelle on 12/28",
                },
                {
                    "OrderNumber": "MC-1007C",
                    "OrderDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "DueDate": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "Contact": "Paid In Full Note Order",
                    "IsQuote": 0,
                    "Subtotal": 120,
                    "Total": 120,
                    "OrderStatusId": None,
                    "Notes": "Customer paid in full at tasting",
                },
            ],
            expenses_rows=[],
            mileage_rows=[],
        )
        deposit_paid = session.exec(select(Order).where(Order.order_number == "MC-1007B")).one()
        assert deposit_paid.payment_status == PaymentStatus.DEPOSIT_PAID
        assert deposit_paid.status == OrderStatus.IN_PROGRESS

        paid_in_full = session.exec(select(Order).where(Order.order_number == "MC-1007C")).one()
        assert paid_in_full.payment_status == PaymentStatus.PAID_IN_FULL
        assert paid_in_full.status == OrderStatus.COMPLETED


def test_parse_order_items_prefers_specific_names_over_generic_other():
    items = parse_order_items(
        {
            "ProductItems": '[{"ProductType": "Other", "ProductName": "Banana Pudding Cups", "Quantity": 2, "SellingPrice": 6}]',
        },
        subtotal=12,
        total_amount=12,
    )
    assert items == [
        {
            "name": "Banana Pudding Cups",
            "description": None,
            "quantity": 2,
            "unit_price": 6.0,
            "total_price": 12.0,
        }
    ]


def test_importer_cli_runs_without_needing_pythonpath():
    backend_dir = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/import_marvelous_creations.py", "--help"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Import Marvelous Creations XLSX data into BakeMate." in result.stdout
