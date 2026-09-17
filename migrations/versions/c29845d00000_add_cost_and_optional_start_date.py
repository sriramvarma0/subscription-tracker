"""Add cost column and make start_date nullable

Revision ID: c29845d00000
Revises: b18742c90000
Create Date: 2026-09-17 15:34:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c29845d00000'
down_revision = 'b18742c90000'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost', sa.Float(), nullable=True))
        batch_op.alter_column('start_date',
               existing_type=sa.DATE(),
               nullable=True)


def downgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.alter_column('start_date',
               existing_type=sa.DATE(),
               nullable=False)
        batch_op.drop_column('cost')
