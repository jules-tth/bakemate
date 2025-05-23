from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
from uuid import UUID
from datetime import date
from pathlib import Path

from sqlmodel import Session
from fastapi.responses import FileResponse

from app.repositories.sqlite_adapter import get_session
from app.services.expense_service import ExpenseService, RECEIPT_STORAGE_PATH
from app.models.expense import Expense, ExpenseCreate, ExpenseRead, ExpenseUpdate, ExpenseCategory
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    *, 
    session: Session = Depends(get_session),
    # Use Form for multipart/form-data when including files
    date_in: date = Form(..., alias="date"),
    description_in: str = Form(..., alias="description"),
    amount_in: float = Form(..., alias="amount"),
    category_in: Optional[ExpenseCategory] = Form(ExpenseCategory.OTHER, alias="category"),
    vendor_in: Optional[str] = Form(None, alias="vendor"),
    notes_in: Optional[str] = Form(None, alias="notes"),
    receipt_file: Optional[UploadFile] = File(None, alias="receipt"), # Alias to match form field name
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new expense for the authenticated user, optionally with a receipt upload.
    Max receipt size: 3MB.
    """
    if receipt_file and receipt_file.size > 3 * 1024 * 1024: # 3MB limit
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Receipt file size exceeds 3MB limit.")

    expense_in = ExpenseCreate(
        user_id=current_user.id,
        date=date_in,
        description=description_in,
        amount=amount_in,
        category=category_in,
        vendor=vendor_in,
        notes=notes_in
        # receipt_filename will be handled by the service if file is provided
    )
    
    expense_service = ExpenseService(session=session)
    new_expense = await expense_service.create_expense(expense_in=expense_in, current_user=current_user, receipt_file=receipt_file)
    return new_expense

@router.get("/", response_model=List[ExpenseRead])
async def read_expenses(
    *, 
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    category: Optional[ExpenseCategory] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve expenses for the authenticated user, with optional filters.
    """
    expense_service = ExpenseService(session=session)
    expenses = await expense_service.get_expenses_by_user(
        current_user=current_user, category=category, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return expenses

@router.get("/{expense_id}", response_model=ExpenseRead)
async def read_expense(
    *, 
    session: Session = Depends(get_session),
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific expense by ID for the authenticated user.
    """
    expense_service = ExpenseService(session=session)
    expense = await expense_service.get_expense_by_id(expense_id=expense_id, current_user=current_user)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found or not owned by user")
    return expense

@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    *, 
    session: Session = Depends(get_session),
    expense_id: UUID,
    # Use Form for multipart/form-data when including files
    date_in: Optional[date] = Form(None, alias="date"),
    description_in: Optional[str] = Form(None, alias="description"),
    amount_in: Optional[float] = Form(None, alias="amount"),
    category_in: Optional[ExpenseCategory] = Form(None, alias="category"),
    vendor_in: Optional[str] = Form(None, alias="vendor"),
    notes_in: Optional[str] = Form(None, alias="notes"),
    remove_receipt: Optional[bool] = Form(False, alias="remove_receipt"), # To explicitly remove receipt
    receipt_file: Optional[UploadFile] = File(None, alias="receipt"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an expense for the authenticated user. Can also update/replace or remove the receipt.
    Max receipt size: 3MB.
    """
    if receipt_file and receipt_file.size > 3 * 1024 * 1024: # 3MB limit
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Receipt file size exceeds 3MB limit.")

    update_data = {}
    if date_in is not None: update_data["date"] = date_in
    if description_in is not None: update_data["description"] = description_in
    if amount_in is not None: update_data["amount"] = amount_in
    if category_in is not None: update_data["category"] = category_in
    if vendor_in is not None: update_data["vendor"] = vendor_in
    if notes_in is not None: update_data["notes"] = notes_in
    if remove_receipt: # If true, we signal to service to remove existing receipt
        update_data["receipt_filename"] = None 
        update_data["receipt_s3_key"] = None
        update_data["receipt_url"] = None

    expense_in = ExpenseUpdate(**update_data)
    expense_service = ExpenseService(session=session)
    updated_expense = await expense_service.update_expense(
        expense_id=expense_id, expense_in=expense_in, current_user=current_user, receipt_file=receipt_file
    )
    if not updated_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found or not owned by user")
    return updated_expense

@router.delete("/{expense_id}", response_model=ExpenseRead)
async def delete_expense(
    *, 
    session: Session = Depends(get_session),
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an expense for the authenticated user.
    """
    expense_service = ExpenseService(session=session)
    deleted_expense = await expense_service.delete_expense(expense_id=expense_id, current_user=current_user)
    if not deleted_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found or not owned by user")
    return deleted_expense

# Endpoint to serve receipt files (example, needs proper security and configuration)
# This should ideally be handled by Nginx or a dedicated file server in production.
@router.get("/receipts/{filename}", response_class=FileResponse)
async def get_receipt_file(
    filename: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user) # Ensure user owns the expense this receipt belongs to
):
    """
    Download a receipt file. **Note:** This is a simplified local serving mechanism.
    In production, use a proper file serving solution (e.g., S3 presigned URLs, CDN).
    """
    expense_service = ExpenseService(session=session)
    # This is a simplified check. The service method needs to verify ownership based on filename.
    # A better approach: query DB for expense with receipt_s3_key ending with filename and owned by user.
    # For now, the service method `get_receipt_file_path` is a placeholder.
    
    # Construct the full path based on how it_s stored in ExpenseService
    # This assumes filename is the unique part (e.g., UUID.ext) stored in receipt_s3_key (if local)
    # or just the `filename` if that_s what `receipt_s3_key` points to directly.
    # The `Expense.receipt_s3_key` stores the full path for local files in the current service impl.
    # So, we need to find an expense that has this filename in its receipt_s3_key and belongs to the user.
    
    # This is a simplified and potentially insecure way to get the path.
    # A robust solution would involve looking up the expense by a receipt identifier or the expense_id itself,
    # then checking ownership and constructing the path from a secure base.
    file_path = RECEIPT_STORAGE_PATH / filename 
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Receipt file not found.")

    # Basic security: check if any expense owned by the user has this receipt_s3_key
    # This is still not ideal as filename itself could be manipulated.
    # A better way: /expenses/{expense_id}/receipt endpoint.
    stmt = select(Expense).where(Expense.user_id == current_user.id, Expense.receipt_s3_key == str(file_path))
    expense_record = session.exec(stmt).first()
    if not expense_record:
        raise HTTPException(status_code=403, detail="Receipt not found or not authorized for this user.")

    return FileResponse(path=file_path, filename=expense_record.receipt_filename or filename, media_type=
                        ("image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) 
                         else "image/png" if filename.lower().endswith('.png') 
                         else "application/pdf" if filename.lower().endswith('.pdf') 
                         else "application/octet-stream"))

