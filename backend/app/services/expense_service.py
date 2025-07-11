from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

from sqlmodel import Session, select

from app.models.expense import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory
from app.models.user import User
from app.repositories.sqlite_adapter import SQLiteRepository

# TODO: Implement cloud storage integration (e.g., AWS S3) for receipts
# Use presigned URLs for secure access and management.

import shutil
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

# Define a base path for storing receipts if not using S3
# This should be configurable and ideally outside the app code (e.g., via settings)
RECEIPT_STORAGE_PATH = Path(settings.APP_FILES_DIR) / "receipts"
RECEIPT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


class ExpenseService:
    def __init__(self, session: Session):
        self.expense_repo = SQLiteRepository(model=Expense)  # type: ignore
        self.session = session

    async def create_expense(
        self,
        *,
        expense_in: ExpenseCreate,
        current_user: User,
        receipt_file: Optional[UploadFile] = None,
    ) -> Expense:
        if expense_in.user_id != current_user.id:
            # Handle error or override user_id
            pass

        expense_data = expense_in.model_dump(exclude_unset=True)
        if (
            "receipt_filename" in expense_data
        ):  # Remove if it was part of Pydantic model but not for DB initially
            del expense_data["receipt_filename"]

        db_expense = Expense(**expense_data)

        if receipt_file:
            # Secure filename and save the file
            # For simplicity, using UUID for filename to avoid collisions
            file_extension = (
                Path(receipt_file.filename).suffix if receipt_file.filename else ".dat"
            )
            saved_filename = f"{UUID.uuid4()}{file_extension}"
            file_location = RECEIPT_STORAGE_PATH / saved_filename

            try:
                with open(file_location, "wb+") as file_object:
                    shutil.copyfileobj(receipt_file.file, file_object)
                db_expense.receipt_filename = (
                    receipt_file.filename
                )  # Store original filename
                db_expense.receipt_s3_key = str(
                    file_location
                )  # Store path as key for local storage
                # In a real S3 setup, this would be the S3 key, and receipt_url would be S3 URL
                db_expense.receipt_url = (
                    f"/files/receipts/{saved_filename}"  # Example local URL
                )
            except Exception as e:
                # Handle file saving error
                print(f"Error saving receipt: {e}")
                # Potentially raise an error or proceed without receipt
                pass
            finally:
                if hasattr(receipt_file, "file") and receipt_file.file:
                    receipt_file.file.close()

        self.session.add(db_expense)
        self.session.commit()
        self.session.refresh(db_expense)
        return db_expense

    async def get_expense_by_id(
        self, *, expense_id: UUID, current_user: User
    ) -> Optional[Expense]:
        expense = await self.expense_repo.get(id=expense_id)
        if expense and expense.user_id == current_user.id:
            return expense
        return None

    async def get_expenses_by_user(
        self,
        *,
        current_user: User,
        category: Optional[ExpenseCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Expense]:
        filters: Dict[str, Any] = {"user_id": current_user.id}
        if category:
            filters["category"] = category
        if start_date:
            filters["date__gte"] = start_date
        if end_date:
            filters["date__lte"] = end_date

        expenses = await self.expense_repo.get_multi(
            filters=filters, skip=skip, limit=limit, sort_by="date", sort_desc=True
        )
        return expenses

    async def update_expense(
        self,
        *,
        expense_id: UUID,
        expense_in: ExpenseUpdate,
        current_user: User,
        receipt_file: Optional[UploadFile] = None,
    ) -> Optional[Expense]:
        db_expense = await self.expense_repo.get(id=expense_id)
        if not db_expense or db_expense.user_id != current_user.id:
            return None

        update_data = expense_in.model_dump(exclude_unset=True)
        # Remove receipt fields from direct update_data if they are handled separately
        update_data.pop("receipt_filename", None)
        update_data.pop("receipt_s3_key", None)
        update_data.pop("receipt_url", None)

        for key, value in update_data.items():
            setattr(db_expense, key, value)

        if receipt_file:
            # Delete old receipt file if it exists and is different
            if db_expense.receipt_s3_key and Path(db_expense.receipt_s3_key).exists():
                try:
                    Path(db_expense.receipt_s3_key).unlink()
                except OSError as e:
                    print(
                        f"Error deleting old receipt {db_expense.receipt_s3_key}: {e}"
                    )

            file_extension = (
                Path(receipt_file.filename).suffix if receipt_file.filename else ".dat"
            )
            saved_filename = f"{UUID.uuid4()}{file_extension}"
            file_location = RECEIPT_STORAGE_PATH / saved_filename
            try:
                with open(file_location, "wb+") as file_object:
                    shutil.copyfileobj(receipt_file.file, file_object)
                db_expense.receipt_filename = receipt_file.filename
                db_expense.receipt_s3_key = str(file_location)
                db_expense.receipt_url = f"/files/receipts/{saved_filename}"
            except Exception as e:
                print(f"Error saving new receipt: {e}")
                pass
            finally:
                if hasattr(receipt_file, "file") and receipt_file.file:
                    receipt_file.file.close()
        elif (
            expense_in.receipt_filename is None and expense_in.receipt_s3_key is None
        ):  # Explicitly removing receipt
            if db_expense.receipt_s3_key and Path(db_expense.receipt_s3_key).exists():
                try:
                    Path(db_expense.receipt_s3_key).unlink()
                except OSError as e:
                    print(f"Error deleting receipt {db_expense.receipt_s3_key}: {e}")
            db_expense.receipt_filename = None
            db_expense.receipt_s3_key = None
            db_expense.receipt_url = None

        self.session.add(db_expense)
        self.session.commit()
        self.session.refresh(db_expense)
        return db_expense

    async def delete_expense(
        self, *, expense_id: UUID, current_user: User
    ) -> Optional[Expense]:
        db_expense = await self.expense_repo.get(id=expense_id)
        if not db_expense or db_expense.user_id != current_user.id:
            return None

        # Delete associated receipt file if it exists
        if db_expense.receipt_s3_key and Path(db_expense.receipt_s3_key).exists():
            try:
                Path(db_expense.receipt_s3_key).unlink()
            except OSError as e:
                print(
                    f"Error deleting receipt file {db_expense.receipt_s3_key} during expense deletion: {e}"
                )

        deleted_expense = await self.expense_repo.delete(id=expense_id)
        return deleted_expense

    # Placeholder for serving receipt files if stored locally
    # This would typically be handled by a static file serving endpoint in main.py
    # or a dedicated file serving microservice / CDN.
    def get_receipt_file_path(
        self, filename: str, current_user: User
    ) -> Optional[Path]:
        # Security check: ensure filename is safe and user has access
        # This is a very basic example and needs proper path traversal protection etc.
        file_path = RECEIPT_STORAGE_PATH / filename
        # Check if the expense associated with this file_path (via db_expense.receipt_s3_key) belongs to current_user
        # For now, just check existence.
        if file_path.exists() and file_path.is_file():
            # Add a check here to ensure the user owns the expense this receipt belongs to.
            # This requires querying the DB for an expense with receipt_s3_key == str(file_path)
            # and user_id == current_user.id.
            return file_path
        return None
