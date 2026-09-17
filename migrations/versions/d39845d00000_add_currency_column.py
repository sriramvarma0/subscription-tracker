"""Add currency column to subscriptions table

Revision ID: d39845d00000
Revises: c29845d00000
Create Date: 2026-09-17 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd39845d00000'
down_revision = 'c29845d00000'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'))


def downgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_column('currency')
