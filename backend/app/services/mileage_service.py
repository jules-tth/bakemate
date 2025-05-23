from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

from sqlmodel import Session, select

from app.models.mileage import MileageLog, MileageLogCreate, MileageLogUpdate
from app.models.user import User
from app.repositories.sqlite_adapter import SQLiteRepository
from app.core.config import settings # For default reimbursement rate

class MileageService:
    def __init__(self, session: Session):
        self.mileage_repo = SQLiteRepository(model=MileageLog) # type: ignore
        self.session = session

    async def _calculate_reimbursement(self, distance: float, rate: Optional[float], current_user: User) -> Optional[float]:
        # Use provided rate, or user-specific default, or system default
        # For now, let_s assume a system default if no rate is provided.
        # A more complex system would fetch user_settings.mileage_rate.
        effective_rate = rate if rate is not None else settings.DEFAULT_MILEAGE_REIMBURSEMENT_RATE
        if effective_rate is not None:
            return round(distance * effective_rate, 2)
        return None

    async def create_mileage_log(self, *, log_in: MileageLogCreate, current_user: User) -> MileageLog:
        if log_in.user_id != current_user.id:
            # Handle error or override user_id
            pass
        
        log_data = log_in.model_dump(exclude_unset=True)
        db_log = MileageLog(**log_data)

        # Calculate reimbursement amount
        db_log.reimbursement_amount = await self._calculate_reimbursement(
            distance=db_log.distance, 
            rate=log_in.reimbursement_rate, # Use rate from input if provided
            current_user=current_user
        )

        self.session.add(db_log)
        self.session.commit()
        self.session.refresh(db_log)
        return db_log

    async def get_mileage_log_by_id(self, *, log_id: UUID, current_user: User) -> Optional[MileageLog]:
        log = await self.mileage_repo.get(id=log_id)
        if log and log.user_id == current_user.id:
            return log
        return None

    async def get_mileage_logs_by_user(
        self, *, current_user: User, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        purpose: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> List[MileageLog]:
        filters: Dict[str, Any] = {"user_id": current_user.id}
        if start_date:
            filters["date__gte"] = start_date
        if end_date:
            filters["date__lte"] = end_date
        if purpose:
            # This would require a more flexible filter (e.g., purpose__icontains=purpose)
            # For exact match:
            filters["purpose"] = purpose 
            
        logs = await self.mileage_repo.get_multi(
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by="date",
            sort_desc=True
        )
        return logs

    async def update_mileage_log(
        self, *, log_id: UUID, log_in: MileageLogUpdate, current_user: User
    ) -> Optional[MileageLog]:
        db_log = await self.mileage_repo.get(id=log_id)
        if not db_log or db_log.user_id != current_user.id:
            return None

        update_data = log_in.model_dump(exclude_unset=True)
        recalculate_reimbursement = False

        for key, value in update_data.items():
            setattr(db_log, key, value)
            if key in ["distance", "reimbursement_rate"]:
                recalculate_reimbursement = True
        
        if recalculate_reimbursement:
            db_log.reimbursement_amount = await self._calculate_reimbursement(
                distance=db_log.distance, 
                rate=db_log.reimbursement_rate, # Use the (potentially updated) rate from the log
                current_user=current_user
            )

        self.session.add(db_log)
        self.session.commit()
        self.session.refresh(db_log)
        return db_log

    async def delete_mileage_log(self, *, log_id: UUID, current_user: User) -> Optional[MileageLog]:
        db_log = await self.mileage_repo.get(id=log_id)
        if not db_log or db_log.user_id != current_user.id:
            return None
        deleted_log = await self.mileage_repo.delete(id=log_id)
        return deleted_log

