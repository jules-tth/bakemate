"""
Add import-related columns and contact link.

This migration targets SQLite in dev using batch_alter_table. For Postgres/MySQL,
adjust types (e.g., use UUID) and optionally add explicit FKs.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250911_add_import_columns"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.add_column(sa.Column("customer_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("customer_company", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("delivery_fee", sa.Float(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("discount_amount", sa.Float(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("event_type", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("theme_details", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("customer_id", sa.String(length=36), nullable=True))

    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.add_column(sa.Column("payment_source", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("vat_amount", sa.Float(), nullable=True, server_default="0"))

    with op.batch_alter_table("mileagelog", schema=None) as batch_op:
        batch_op.add_column(sa.Column("order_ref", sa.String(length=64), nullable=True))

    # For non-SQLite DBs, add FK (uncomment and adjust types)
    # op.create_foreign_key(
    #     "fk_order_customer_id_contact",
    #     source_table="order",
    #     referent_table="contact",
    #     local_cols=["customer_id"],
    #     remote_cols=["id"],
    # )


def downgrade() -> None:
    with op.batch_alter_table("mileagelog", schema=None) as batch_op:
        batch_op.drop_column("order_ref")

    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.drop_column("vat_amount")
        batch_op.drop_column("payment_source")

    # op.drop_constraint("fk_order_customer_id_contact", "order", type_="foreignkey")
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.drop_column("customer_id")
        batch_op.drop_column("theme_details")
        batch_op.drop_column("event_type")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("delivery_fee")
        batch_op.drop_column("customer_company")
        batch_op.drop_column("customer_name")

