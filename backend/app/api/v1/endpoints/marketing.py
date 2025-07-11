from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any
from pydantic import BaseModel, EmailStr

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.marketing.marketing_service import MarketingService, MarketingSegment
from app.models.user import User
from app.models.contact import ContactRead  # To show contacts in a segment
from app.auth.dependencies import get_current_active_user

router = APIRouter()


class CampaignBody(BaseModel):
    segment_type: str  # e.g., "top_customers", "dormant_customers"
    subject: str
    html_content: str  # This would be the crafted HTML from a UI


@router.get("/segments/{segment_type}/contacts", response_model=List[ContactRead])
async def get_segment_contacts(
    *,
    session: Session = Depends(get_session),
    segment_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of contacts belonging to a specific marketing segment.
    Valid segment_types: "top_customers", "dormant_customers".
    """
    if segment_type not in [
        MarketingSegment.TOP_CUSTOMERS,
        MarketingSegment.DORMANT_CUSTOMERS,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid segment type."
        )

    marketing_service = MarketingService(session=session)
    contacts = await marketing_service.get_contacts_for_segment(
        segment_type=segment_type, current_user=current_user
    )
    return contacts


@router.post("/campaigns/send", response_model=Dict[str, Any])
async def send_marketing_campaign(
    *,
    session: Session = Depends(get_session),
    campaign_data: CampaignBody = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a marketing campaign to a specified segment.
    The `html_content` should be the fully crafted HTML email body.
    """
    if campaign_data.segment_type not in [
        MarketingSegment.TOP_CUSTOMERS,
        MarketingSegment.DORMANT_CUSTOMERS,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid segment type for campaign.",
        )

    if not campaign_data.subject or not campaign_data.html_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign subject and HTML content are required.",
        )

    marketing_service = MarketingService(session=session)
    result = await marketing_service.send_campaign_to_segment(
        segment_type=campaign_data.segment_type,
        subject=campaign_data.subject,
        html_content=campaign_data.html_content,
        current_user=current_user,
    )
    return result


# Example endpoint to get a basic HTML template (for UI to use/modify)
@router.post("/campaigns/template/basic", response_model=str)
async def get_basic_campaign_template_preview(
    *,
    session: Session = Depends(
        get_session
    ),  # Not strictly needed for this static template
    title: str = Body("Your Special Offer!"),
    body_paragraph: str = Body(
        "We have something amazing just for you. Check it out now before it_s too late!"
    ),
    cta_text: str = Body("Learn More"),
    cta_url: str = Body("https://example.com/offer"),
    current_user: User = Depends(
        get_current_active_user
    )  # To get shop name or user context
):
    """
    Generate a basic HTML email template string.
    The UI would use this as a starting point for crafting an email.
    """
    marketing_service = MarketingService(session=session)
    # Potentially fetch shop_name from user_s shop_configuration if available
    shop_name = current_user.full_name or "Your Bakery"  # Placeholder
    # shop_config = await ShopService(session).get_shop_configuration_by_user(current_user=current_user)
    # if shop_config and shop_config.shop_name:
    #     shop_name = shop_config.shop_name

    html_template = marketing_service.get_basic_campaign_template(
        title=title,
        body_paragraph=body_paragraph,
        cta_text=cta_text,
        cta_url=cta_url,
        shop_name=shop_name,
    )
    return html_template
