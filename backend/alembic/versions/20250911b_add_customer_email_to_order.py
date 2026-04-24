"""
Add customer_email to order table for legacy DBs missing the column.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250911b_add_customer_email_to_order"
down_revision = "20250911_add_import_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.add_column(sa.Column("customer_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.drop_column("customer_email")

