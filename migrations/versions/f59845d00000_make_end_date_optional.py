"""Make end_date optional (nullable=True) for No Expiry subscriptions

Revision ID: f59845d00000
Revises: e49845d00000
Create Date: 2026-09-18 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f59845d00000'
down_revision = 'e49845d00000'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.alter_column('end_date',
               existing_type=sa.DATE(),
               nullable=True)


def downgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.alter_column('end_date',
               existing_type=sa.DATE(),
               nullable=False)
