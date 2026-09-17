"""Add auto_renew and subscription_renewals table

Revision ID: b18742c90000
Revises: a9653bac80e2
Create Date: 2026-09-17 14:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b18742c90000'
down_revision = 'a9653bac80e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auto_renew', sa.String(length=10), nullable=False, server_default='UNKNOWN'))
        batch_op.alter_column('start_date',
               existing_type=sa.DATE(),
               nullable=False)

    op.create_table('subscription_renewals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('previous_end_date', sa.Date(), nullable=True),
        sa.Column('renewed_on', sa.Date(), nullable=False),
        sa.Column('new_start_date', sa.Date(), nullable=False),
        sa.Column('new_end_date', sa.Date(), nullable=False),
        sa.Column('renewal_type', sa.String(length=10), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('subscription_renewals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subscription_renewals_subscription_id'), ['subscription_id'], unique=False)


def downgrade():
    with op.batch_alter_table('subscription_renewals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subscription_renewals_subscription_id'))

    op.drop_table('subscription_renewals')

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_column('auto_renew')
