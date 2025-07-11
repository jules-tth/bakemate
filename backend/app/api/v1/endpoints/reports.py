from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Any, Optional
from datetime import date
from uuid import UUID

from sqlmodel import Session
from fastapi.responses import StreamingResponse, Response  # For CSV and PDF

from app.repositories.sqlite_adapter import get_session
from app.services.report_service import ReportService
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/profit-and-loss", summary="Profit and Loss Report")
async def get_profit_and_loss_report(
    *,
    session: Session = Depends(get_session),
    start_date: date = Query(
        ..., description="Start date for the report period (YYYY-MM-DD)"
    ),
    end_date: date = Query(
        ..., description="End date for the report period (YYYY-MM-DD)"
    ),
    output_format: str = Query(
        "json", enum=["json", "csv", "pdf"], description="Output format for the report"
    ),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a Profit and Loss report for the specified period.
    Output can be JSON, CSV, or PDF (PDF is placeholder).
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date.",
        )

    report_service = ReportService(session=session)
    report_data = await report_service.generate_profit_and_loss_report(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        output_format=output_format,
    )

    if output_format == "csv":
        return report_service.stream_csv_report(
            report_data, f"profit_and_loss_{start_date}_to_{end_date}.csv"
        )
    elif output_format == "pdf":
        # Placeholder for PDF generation
        pdf_bytes = await report_service.generate_pdf_report_placeholder(
            "Profit and Loss Report", report_data
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=pnl_report_{start_date}_to_{end_date}.pdf"
            },
        )
    return report_data  # JSON by default


@router.get("/sales-by-product", summary="Sales by Product Report")
async def get_sales_by_product_report(
    *,
    session: Session = Depends(get_session),
    start_date: date = Query(
        ..., description="Start date for the report period (YYYY-MM-DD)"
    ),
    end_date: date = Query(
        ..., description="End date for the report period (YYYY-MM-DD)"
    ),
    output_format: str = Query(
        "json", enum=["json", "csv", "pdf"], description="Output format for the report"
    ),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a Sales by Product report for the specified period.
    Output can be JSON, CSV, or PDF (PDF is placeholder).
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date.",
        )

    report_service = ReportService(session=session)
    report_data = await report_service.generate_sales_by_product_report(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        output_format=output_format,
    )

    if output_format == "csv":
        return report_service.stream_csv_report(
            report_data, f"sales_by_product_{start_date}_to_{end_date}.csv"
        )
    elif output_format == "pdf":
        pdf_bytes = await report_service.generate_pdf_report_placeholder(
            "Sales by Product Report", report_data
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=sales_by_product_{start_date}_to_{end_date}.pdf"
            },
        )
    return report_data


@router.get("/ingredient-usage", summary="Ingredient Usage Report")
async def get_ingredient_usage_report(
    *,
    session: Session = Depends(get_session),
    start_date: date = Query(
        ..., description="Start date for the report period (YYYY-MM-DD)"
    ),
    end_date: date = Query(
        ..., description="End date for the report period (YYYY-MM-DD)"
    ),
    output_format: str = Query(
        "json", enum=["json", "csv", "pdf"], description="Output format for the report"
    ),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate an Ingredient Usage report based on completed orders for the specified period.
    Output can be JSON, CSV, or PDF (PDF is placeholder).
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date.",
        )

    report_service = ReportService(session=session)
    report_data = await report_service.generate_ingredient_usage_report(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        output_format=output_format,
    )

    if output_format == "csv":
        return report_service.stream_csv_report(
            report_data, f"ingredient_usage_{start_date}_to_{end_date}.csv"
        )
    elif output_format == "pdf":
        pdf_bytes = await report_service.generate_pdf_report_placeholder(
            "Ingredient Usage Report", report_data
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ingredient_usage_{start_date}_to_{end_date}.pdf"
            },
        )
    return report_data


@router.get("/low-stock", summary="Low Stock Report")
async def get_low_stock_report(
    *,
    session: Session = Depends(get_session),
    output_format: str = Query(
        "json", enum=["json", "csv", "pdf"], description="Output format for the report"
    ),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a Low Stock report for ingredients below their threshold.
    Output can be JSON, CSV, or PDF (PDF is placeholder).
    """
    report_service = ReportService(session=session)
    report_data = await report_service.generate_low_stock_report(
        current_user=current_user, output_format=output_format
    )

    if output_format == "csv":
        return report_service.stream_csv_report(report_data, "low_stock_report.csv")
    elif output_format == "pdf":
        pdf_bytes = await report_service.generate_pdf_report_placeholder(
            "Low Stock Report", report_data
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=low_stock_report.pdf"
            },
        )
    return report_data
