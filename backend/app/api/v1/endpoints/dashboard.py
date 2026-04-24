from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.repositories.sqlite_adapter import get_session
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(
    *,
    session: Session = Depends(get_session),
    range: str,
    current_user: User = Depends(get_current_active_user),
):
    service = DashboardService(session)
    return await service.get_summary(current_user=current_user, range=range)


@router.get("/orders")
async def dashboard_orders(
    *,
    session: Session = Depends(get_session),
    range: str,
    current_user: User = Depends(get_current_active_user),
) -> List[dict]:
    service = DashboardService(session)
    return await service.get_orders_over_time(current_user=current_user, range=range)


@router.get("/revenue")
async def dashboard_revenue(
    *,
    session: Session = Depends(get_session),
    range: str,
    current_user: User = Depends(get_current_active_user),
) -> List[dict]:
    service = DashboardService(session)
    return await service.get_revenue_over_time(current_user=current_user, range=range)
