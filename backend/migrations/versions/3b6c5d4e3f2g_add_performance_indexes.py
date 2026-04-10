"""add performance indexes

Revision ID: 3b6c5d4e3f2g
Revises: 2a5e4b3c2d1a
Create Date: 2026-04-09 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b6c5d4e3f2g'
down_revision = '2a5e4b3c2d1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Meals indexes
    op.create_index('idx_meals_user_id', 'meals', ['user_id'], unique=False)
    op.create_index('idx_meals_status', 'meals', ['status'], unique=False)
    op.create_index('idx_meals_created_at', 'meals', ['created_at'], unique=False)
    op.create_index('idx_meals_user_created', 'meals', ['user_id', 'created_at'], unique=False)

    # Steps indexes
    op.create_index('idx_steps_user_id', 'steps', ['user_id'], unique=False)
    op.create_index('idx_steps_date', 'steps', ['date'], unique=False)
    op.create_index('idx_steps_user_date', 'steps', ['user_id', 'date'], unique=False)


def downgrade() -> None:
    # Steps indexes
    op.drop_index('idx_steps_user_date', table_name='steps')
    op.drop_index('idx_steps_date', table_name='steps')
    op.drop_index('idx_steps_user_id', table_name='steps')

    # Meals indexes
    op.drop_index('idx_meals_user_created', table_name='meals')
    op.drop_index('idx_meals_created_at', table_name='meals')
    op.drop_index('idx_meals_status', table_name='meals')
    op.drop_index('idx_meals_user_id', table_name='meals')
