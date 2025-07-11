from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.models.shop.shop_configuration import (
    ShopConfiguration,
    ShopConfigurationCreate,
    ShopConfigurationUpdate,
    ShopProduct,
    PublicShopView,
    PublicShopProductView,
    ShopOrderCreate,
    ShopOrderItemCreate,
    ShopStatus,
)
from app.models.user import User
from app.models.recipe import Recipe  # To fetch recipe details for shop products
from app.models.order import (
    Order,
    OrderCreate,
    OrderItem,
    OrderItemCreate,
    OrderStatus as AppOrderStatus,
)  # Main app order status
from app.repositories.sqlite_adapter import SQLiteRepository
from app.services.order_service import (
    OrderService,
)  # To create orders in the main system
from app.services.email_service import EmailService  # To send confirmation emails
from app.core.config import settings


class ShopService:
    def __init__(self, session: Session):
        self.shop_config_repo = SQLiteRepository(model=ShopConfiguration)  # type: ignore
        self.session = session
        self.order_service = OrderService(
            session=session
        )  # For creating main app orders
        self.email_service = EmailService()  # For notifications

    async def create_shop_configuration(
        self, *, shop_config_in: ShopConfigurationCreate, current_user: User
    ) -> ShopConfiguration:
        if shop_config_in.user_id != current_user.id:
            # This should ideally be set by the system or validated strictly
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create shop configuration for another user.",
            )

        # Check if slug is unique for this user (or globally, depending on design)
        # For now, assuming slug must be globally unique as it forms part of URL.
        existing_slug_stmt = select(ShopConfiguration).where(
            ShopConfiguration.shop_slug == shop_config_in.shop_slug
        )
        if self.session.exec(existing_slug_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shop slug {shop_config_in.shop_slug} already exists.",
            )

        # User can only have one shop configuration for now
        existing_shop_stmt = select(ShopConfiguration).where(
            ShopConfiguration.user_id == current_user.id
        )
        if self.session.exec(existing_shop_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User can only have one shop configuration. Update the existing one.",
            )

        shop_data = shop_config_in.model_dump(exclude_unset=True, exclude={"products"})
        db_shop_config = ShopConfiguration(**shop_data)

        if shop_config_in.products:
            # Validate products - e.g., ensure recipes exist and belong to the user
            valid_shop_products = []
            for prod_in in shop_config_in.products:
                recipe = self.session.get(Recipe, prod_in.recipe_id)
                if not recipe or recipe.user_id != current_user.id:
                    # Skip or raise error for invalid recipe ID
                    continue
                # Ensure price is positive
                if prod_in.price < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product price for {prod_in.name} cannot be negative.",
                    )
                valid_shop_products.append(prod_in)
            db_shop_config.set_products(valid_shop_products)

        self.session.add(db_shop_config)
        self.session.commit()
        self.session.refresh(db_shop_config)
        return db_shop_config

    async def get_shop_configuration_by_user(
        self, *, current_user: User
    ) -> Optional[ShopConfiguration]:
        statement = select(ShopConfiguration).where(
            ShopConfiguration.user_id == current_user.id
        )
        shop_config = self.session.exec(statement).first()
        return shop_config

    async def get_shop_configuration_by_slug(
        self, *, shop_slug: str
    ) -> Optional[ShopConfiguration]:
        statement = select(ShopConfiguration).where(
            ShopConfiguration.shop_slug == shop_slug
        )
        shop_config = self.session.exec(statement).first()
        return shop_config

    async def update_shop_configuration(
        self,
        *,
        shop_config_id: UUID,
        shop_config_in: ShopConfigurationUpdate,
        current_user: User,
    ) -> Optional[ShopConfiguration]:
        db_shop_config = self.session.get(ShopConfiguration, shop_config_id)
        if not db_shop_config or db_shop_config.user_id != current_user.id:
            return None

        update_data = shop_config_in.model_dump(
            exclude_unset=True, exclude={"products"}
        )

        if (
            "shop_slug" in update_data
            and update_data["shop_slug"] != db_shop_config.shop_slug
        ):
            existing_slug_stmt = select(ShopConfiguration).where(
                ShopConfiguration.shop_slug == update_data["shop_slug"]
            )
            if self.session.exec(existing_slug_stmt).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shop slug {update_data['shop_slug']} already exists.",
                )

        for key, value in update_data.items():
            setattr(db_shop_config, key, value)

        if (
            shop_config_in.products is not None
        ):  # Allows clearing products with an empty list
            valid_shop_products = []
            for prod_in in shop_config_in.products:
                recipe = self.session.get(Recipe, prod_in.recipe_id)
                if not recipe or recipe.user_id != current_user.id:
                    continue
                if prod_in.price < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product price for {prod_in.name} cannot be negative.",
                    )
                valid_shop_products.append(prod_in)
            db_shop_config.set_products(valid_shop_products)

        self.session.add(db_shop_config)
        self.session.commit()
        self.session.refresh(db_shop_config)
        return db_shop_config

    async def delete_shop_configuration(
        self, *, shop_config_id: UUID, current_user: User
    ) -> Optional[ShopConfiguration]:
        db_shop_config = self.session.get(ShopConfiguration, shop_config_id)
        if not db_shop_config or db_shop_config.user_id != current_user.id:
            return None
        self.session.delete(db_shop_config)
        self.session.commit()
        return db_shop_config  # Return the deleted object, or just a success message

    async def get_public_shop_view(self, *, shop_slug: str) -> Optional[PublicShopView]:
        shop_config = await self.get_shop_configuration_by_slug(shop_slug=shop_slug)
        if (
            not shop_config
            or shop_config.status != ShopStatus.ACTIVE
            or not shop_config.allow_online_orders
        ):
            return None  # Or raise 404 / specific error

        public_products = []
        for shop_product_data in shop_config.products_json or []:
            shop_product = ShopProduct(**shop_product_data)
            if shop_product.is_available:
                # Fetch recipe details if needed, or assume ShopProduct has enough info
                public_products.append(
                    PublicShopProductView(
                        recipe_id=shop_product.recipe_id,
                        name=shop_product.name,
                        price=shop_product.price,
                        description=shop_product.description,
                        image_url=shop_product.image_url,
                    )
                )

        return PublicShopView(
            shop_name=shop_config.shop_name,
            description=shop_config.description,
            logo_url=shop_config.logo_url,
            contact_email=shop_config.contact_email,
            theme_color_primary=shop_config.theme_color_primary,
            theme_color_secondary=shop_config.theme_color_secondary,
            products=public_products,
            delivery_options=shop_config.delivery_options,
            min_order_amount=shop_config.min_order_amount,
        )

    async def create_order_from_shop(self, *, order_in: ShopOrderCreate) -> Order:
        shop_config = await self.get_shop_configuration_by_slug(
            shop_slug=order_in.shop_slug
        )
        if (
            not shop_config
            or shop_config.status != ShopStatus.ACTIVE
            or not shop_config.allow_online_orders
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found or not accepting orders.",
            )

        baker_user = self.session.get(User, shop_config.user_id)
        if not baker_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Shop owner not found.",
            )

        order_items_create: List[OrderItemCreate] = []
        shop_products_map = {
            str(p["recipe_id"]): ShopProduct(**p)
            for p in (shop_config.products_json or [])
        }

        for item_in in order_in.items:
            shop_product = shop_products_map.get(str(item_in.recipe_id))
            if not shop_product or not shop_product.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product ID {item_in.recipe_id} not available or not found in shop.",
                )

            item_total_price = Decimal(shop_product.price) * Decimal(item_in.quantity)
            total_order_amount += item_total_price

            # Fetch recipe to get its current cost for COGS if possible
            recipe_details = self.session.get(Recipe, item_in.recipe_id)
            item_cost_price = (
                recipe_details.cost_price if recipe_details else Decimal(0)
            )  # Simplified COGS

            order_items_create.append(
                OrderItemCreate(
                    recipe_id=item_in.recipe_id,
                    name=shop_product.name,  # Denormalized name from shop product
                    quantity=item_in.quantity,
                    unit_price=Decimal(shop_product.price),
                    total_price=item_total_price,
                    cost_price=item_cost_price,  # Store cost at time of order for P&L
                )
            )

        if shop_config.min_order_amount and total_order_amount < Decimal(
            shop_config.min_order_amount
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order total is below minimum of {shop_config.min_order_amount}.",
            )
        if shop_config.max_order_amount and total_order_amount > Decimal(
            shop_config.max_order_amount
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order total exceeds maximum of {shop_config.max_order_amount}.",
            )
        if shop_config.max_order_amount and total_order_amount > Decimal(
            shop_config.max_order_amount
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order total exceeds maximum of {shop_config.max_order_amount}.",
            )

        # Create the main application order
        main_order_create = OrderCreate(
            user_id=baker_user.id,  # Order belongs to the baker
            customer_name=order_in.customer_name,
            customer_email=order_in.customer_email,
            customer_phone=order_in.customer_phone,
            # order_date is set by default in Order model
            due_date=datetime.now(timezone.utc).date()
            + timedelta(days=3),  # Example: default due date 3 days from now
            total_amount=total_order_amount,
            status=AppOrderStatus.NEW_ONLINE,  # Special status for shop orders
            notes=f"Order placed via online shop: {order_in.shop_slug}. Pickup: {order_in.pickup_time_slot if order_in.pickup_time_slot else 'N/A'}",
            items=order_items_create,
            # payment_status, deposit_amount etc. would be handled by Stripe flow later
            # payment_status, deposit_amount etc. would be handled by Stripe flow later
        )

        created_order = await self.order_service.create_order(
            order_in=main_order_create, current_user=baker_user, skip_stripe=True
        )

        # Send confirmation emails (to customer and baker)
        try:
            await self.email_service.send_shop_order_confirmation_to_customer(
                to_email=order_in.customer_email,
                customer_name=order_in.customer_name,
                order_id=created_order.id,
                shop_name=shop_config.shop_name or "Your Bakery",
                order_details_html="<p>Details about your order...</p>",  # Generate proper HTML
            )
            await self.email_service.send_new_shop_order_to_baker(
                to_email=baker_user.email,  # Baker's email
                baker_name=baker_user.full_name or baker_user.email,
                order_id=created_order.id,
                customer_name=order_in.customer_name,
                shop_name=shop_config.shop_name or "Your Bakery",
            )
        except Exception as e:
            print(f"Failed to send shop order confirmation emails: {e}")
            # Log this error, but don't fail the order creation

        return created_order

        return created_order

    async def get_embed_snippet(self, *, shop_slug: str, current_user: User) -> str:
        shop_config = await self.get_shop_configuration_by_slug(shop_slug=shop_slug)
        if not shop_config or shop_config.user_id != current_user.id:
            return ""  # or raise HTTPException(status_code=403, detail="Not authorized to access this shop embed snippet.")
        # In a real app, this would point to a JS bundle hosted on a CDN or the app itself.
        # The JS would then render the shop form.
        # For now, it's a conceptual placeholder.
        base_url = (
            settings.SERVER_HOST
        )  # e.g., http://localhost:8000 or https://bakemate.app
        shop_url = f"{base_url}/api/v1/shop/public/{shop_slug}"  # This is the API endpoint for public view
        # A true embed would likely be a JS widget that calls this API.
        # For a simple iframe embed:
        iframe_embed_url = f"{base_url}/shop-embed/{shop_slug}"  # A dedicated frontend route for embedding

        snippet = f'<div id="bakemate-shop-{shop_slug}"></div>\n'
        snippet += f'<script src="{base_url}/static/js/bakemate-shop-embed.js" '
        snippet += f'data-shop-slug="{shop_slug}" data-target-div="bakemate-shop-{shop_slug}" async defer></script>'

        # Simpler iframe version for now if direct JS embed is too complex for this stage:
        # snippet = f'<iframe src="{iframe_embed_url}" width="100%" height="600px" frameborder="0"></iframe>'
        return snippet
        # snippet = f'<iframe src="{iframe_embed_url}" width="100%" height="600px" frameborder="0"></iframe>'
        return snippet
