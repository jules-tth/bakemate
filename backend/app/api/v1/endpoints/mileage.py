from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from uuid import UUID
from datetime import date

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.mileage_service import MileageService
from app.models.mileage import (
    MileageLog,
    MileageLogCreate,
    MileageLogRead,
    MileageLogUpdate,
)
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.post("/import", response_model=dict)
async def import_mileage_from_csv(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Import mileage logs from CSV located under `tmp/import_data/*Mileage*.csv`.
    Expects headers: Date, Purpose, Miles, Description (others ignored).
    """
    import csv
    from datetime import datetime
    from pathlib import Path

    def resolve_import_dir() -> Path:
        candidates = [
            Path("tmp/import_data"),
            Path(__file__).resolve().parents[5] / "tmp/import_data",
            Path(__file__).resolve().parents[4] / "tmp/import_data",
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]

    def parse_date(value: str):
        value = (value or "").strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        raise ValueError(f"Unrecognized date format: {value}")

    import_dir = resolve_import_dir()
    matches = list(import_dir.glob("*Mileage*.csv"))
    if not matches:
        return {"imported": 0, "skipped": 0, "errors": ["No Mileage CSV found."], "files": []}

    mileage_service = MileageService(session=session)
    imported = 0
    skipped = 0
    errors = []
    files = []

    for file_path in matches:
        files.append(str(file_path))
        try:
            with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, start=2):
                    try:
                        date_val = parse_date(row.get("Date", ""))
                        purpose = (row.get("Purpose") or "").strip() or None
                        miles_raw = (row.get("Miles") or row.get("Distance") or "0").replace(",", "").strip()
                        distance = float(miles_raw or 0)
                        order_ref = (row.get("OrderRef") or "").strip() or None
                        notes = (row.get("Description") or "").strip() or None

                        log_in = MileageLogCreate(
                            user_id=current_user.id,
                            date=date_val,
                            distance=distance,
                            purpose=purpose,
                            order_ref=order_ref,
                            notes=notes,
                        )
                        await mileage_service.create_mileage_log(
                            log_in=log_in, current_user=current_user
                        )
                        imported += 1
                    except Exception as e:
                        skipped += 1
                        errors.append(f"{file_path.name} line {idx}: {e}")
        except Exception as e:
            errors.append(f"Failed to process {file_path.name}: {e}")

    return {"imported": imported, "skipped": skipped, "errors": errors, "files": files}

@router.post("/", response_model=MileageLogRead, status_code=status.HTTP_201_CREATED)
async def create_mileage_log(
    *,
    session: Session = Depends(get_session),
    log_in: MileageLogCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new mileage log for the authenticated user.
    """
    if log_in.user_id != current_user.id:
        # This should be handled by service or pre-validation
        pass
    mileage_service = MileageService(session=session)
    new_log = await mileage_service.create_mileage_log(
        log_in=log_in, current_user=current_user
    )
    return new_log


@router.get("/", response_model=List[MileageLogRead])
async def read_mileage_logs(
    *,
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    purpose: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve mileage logs for the authenticated user, with optional filters.
    """
    mileage_service = MileageService(session=session)
    logs = await mileage_service.get_mileage_logs_by_user(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        purpose=purpose,
        skip=skip,
        limit=limit,
    )
    return logs


@router.get("/{log_id}", response_model=MileageLogRead)
async def read_mileage_log(
    *,
    session: Session = Depends(get_session),
    log_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific mileage log by ID for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    log = await mileage_service.get_mileage_log_by_id(
        log_id=log_id, current_user=current_user
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mileage log not found or not owned by user",
        )
    return log


@router.put("/{log_id}", response_model=MileageLogRead)
async def update_mileage_log(
    *,
    session: Session = Depends(get_session),
    log_id: UUID,
    log_in: MileageLogUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a mileage log for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    updated_log = await mileage_service.update_mileage_log(
        log_id=log_id, log_in=log_in, current_user=current_user
    )
    if not updated_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mileage log not found or not owned by user",
        )
    return updated_log


@router.delete("/{log_id}", response_model=MileageLogRead)
async def delete_mileage_log(
    *,
    session: Session = Depends(get_session),
    log_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a mileage log for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    deleted_log = await mileage_service.delete_mileage_log(
        log_id=log_id, current_user=current_user
    )
    if not deleted_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mileage log not found or not owned by user",
        )
    return deleted_log


@router.post("/import-file", response_model=dict)
async def import_mileage_file(
    *,
    session: Session = Depends(get_session),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    Import mileage logs from an uploaded CSV file.
    """
    import csv, io
    from datetime import datetime

    def parse_date(value: str):
        value = (value or "").strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        raise ValueError(f"Unrecognized date format: {value}")

    mileage_service = MileageService(session=session)
    imported = 0
    skipped = 0
    errors: list[str] = []

    text_stream = io.TextIOWrapper(file.file, encoding="utf-8")
    reader = csv.DictReader(text_stream)
    for idx, row in enumerate(reader, start=2):
        try:
            date_val = parse_date(row.get("Date", ""))
            purpose = (row.get("Purpose") or "").strip() or None
            miles_raw = (row.get("Miles") or row.get("Distance") or "0").replace(",", "").strip()
            distance = float(miles_raw or 0)
            order_ref = (row.get("OrderRef") or "").strip() or None
            notes = (row.get("Description") or "").strip() or None
            log_in = MileageLogCreate(
                user_id=current_user.id,
                date=date_val,
                distance=distance,
                purpose=purpose,
                order_ref=order_ref,
                notes=notes,
            )
            await mileage_service.create_mileage_log(
                log_in=log_in, current_user=current_user
            )
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"line {idx}: {e}")

    return {"imported": imported, "skipped": skipped, "errors": errors}
