"""add status to meals

Revision ID: 8e44c21a4f0b
Revises: 7f83a4d8c1e2
Create Date: 2026-04-09 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e44c21a4f0b'
down_revision = '7f83a4d8c1e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status column to meals table
    op.add_column('meals', sa.Column('status', sa.String(), nullable=True, server_default='processing'))


def downgrade() -> None:
    # Remove status column from meals table
    op.drop_column('meals', 'status')
