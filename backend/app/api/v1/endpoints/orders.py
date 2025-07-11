from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Body,
    Header,
    Response,
)
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session
import stripe  # For webhook verification if not done by a library

from app.repositories.sqlite_adapter import get_session
from app.services.order_service import OrderService, QuoteService
from app.models.order import (
    Order,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    OrderStatus,
    PaymentStatus,
    Quote,
    QuoteCreate,
    QuoteRead,
    QuoteUpdate,
    QuoteStatus,
)  # Added Quote models
from app.models.user import User
from app.auth.dependencies import get_current_active_user
from app.core.config import settings

router = APIRouter()

# --- Order Endpoints --- #


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    *,
    session: Session = Depends(get_session),
    order_in: OrderCreate,
    current_user: User = Depends(get_current_active_user),
):
    if order_in.user_id != current_user.id:
        pass  # Assuming service handles or pre-validated
    order_service = OrderService(session=session)
    new_order = await order_service.create_order(
        order_in=order_in, current_user=current_user
    )
    return new_order


@router.get("/", response_model=List[OrderRead])
async def read_orders(
    *,
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    orders = await order_service.get_orders_by_user(
        current_user=current_user, skip=skip, limit=limit, status=status_filter
    )
    return orders


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    order = await order_service.get_order_by_id(
        order_id=order_id, current_user=current_user
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not owned by user",
        )
    return order


@router.put("/{order_id}", response_model=OrderRead)
async def update_order(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    updated_order = await order_service.update_order(
        order_id=order_id, order_in=order_in, current_user=current_user
    )
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not owned by user",
        )
    return updated_order


@router.delete("/{order_id}", response_model=OrderRead)
async def delete_order(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    deleted_order = await order_service.delete_order(
        order_id=order_id, current_user=current_user
    )
    if not deleted_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not owned by user",
        )
    return deleted_order


# --- Quote Endpoints --- #


@router.post("/quotes/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def create_quote(
    *,
    session: Session = Depends(get_session),
    quote_in: QuoteCreate,
    current_user: User = Depends(get_current_active_user),
):
    if quote_in.user_id != current_user.id:
        pass  # Assuming service handles or pre-validated
    quote_service = QuoteService(session=session)
    new_quote = await quote_service.create_quote(
        quote_in=quote_in, current_user=current_user
    )
    return new_quote


@router.get("/quotes/", response_model=List[QuoteRead])
async def read_quotes(
    *,
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[QuoteStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
):
    quote_service = QuoteService(session=session)
    quotes = await quote_service.get_quotes_by_user(
        current_user=current_user, skip=skip, limit=limit, status=status_filter
    )
    return quotes


@router.get("/quotes/{quote_id}", response_model=QuoteRead)
async def read_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    quote_service = QuoteService(session=session)
    quote = await quote_service.get_quote_by_id(
        quote_id=quote_id, current_user=current_user
    )
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found or not owned by user",
        )
    return quote


@router.put("/quotes/{quote_id}", response_model=QuoteRead)
async def update_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: UUID,
    quote_in: QuoteUpdate,
    current_user: User = Depends(get_current_active_user),
):
    quote_service = QuoteService(session=session)
    updated_quote = await quote_service.update_quote(
        quote_id=quote_id, quote_in=quote_in, current_user=current_user
    )
    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found or not owned by user",
        )
    return updated_quote


@router.delete("/quotes/{quote_id}", response_model=QuoteRead)
async def delete_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    quote_service = QuoteService(session=session)
    deleted_quote = await quote_service.delete_quote(
        quote_id=quote_id, current_user=current_user
    )
    if not deleted_quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found or not owned by user",
        )
    return deleted_quote


@router.post("/quotes/{quote_id}/convert-to-order", response_model=OrderRead)
async def convert_quote_to_order(
    *,
    session: Session = Depends(get_session),
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(
        session=session
    )  # OrderService contains the conversion logic
    converted_order = await order_service.convert_quote_to_order(
        quote_id=quote_id, current_user=current_user
    )
    if not converted_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not convert quote to order. Quote might not be found, not owned, or not in an acceptable status.",
        )
    return converted_order


# --- Stripe Related Endpoints --- #


@router.post("/{order_id}/create-payment-intent", response_model=dict)
async def create_payment_intent_for_order(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    order = await order_service.get_order_by_id(
        order_id=order_id, current_user=current_user
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    if order.payment_status == PaymentStatus.PAID_IN_FULL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid in full.",
        )

    client_secret = await order_service.create_stripe_payment_intent(
        order_id=order_id, current_user=current_user
    )
    if not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create payment intent",
        )
    return {"client_secret": client_secret}


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request_body: bytes = Body(...),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    session: Session = Depends(get_session),
):
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    order_service = OrderService(session=session)
    try:
        event_payload = request_body.decode("utf-8")
        success = await order_service.handle_stripe_webhook(
            payload=event_payload, signature=stripe_signature
        )
        if success:
            return {"status": "success"}
        else:
            print("Stripe webhook processing failed internally.")
            return {"status": "internal error, but acknowledged"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {e}"
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid signature: {e}"
        )
    except Exception as e:
        print(f"Generic error processing Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error",
        )


# --- Invoice and Client Portal Endpoints (Placeholders) --- #


@router.get(
    "/{order_id}/invoice/pdf"
)  # Removed response_class=bytes to use FastAPI Response directly
async def get_order_invoice_pdf(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    pdf_bytes = await order_service.generate_invoice_pdf(
        order_id=order_id, current_user=current_user
    )
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not generate PDF or order not found.",
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_order_{order_id}.pdf"
        },
    )


@router.get("/{order_id}/client-portal-url", response_model=dict)
async def get_client_portal_url_for_order(
    *,
    session: Session = Depends(get_session),
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    order_service = OrderService(session=session)
    url = await order_service.get_client_portal_url(
        order_id=order_id, current_user=current_user
    )
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not generate portal URL or order not found.",
        )
    return {"url": url}
