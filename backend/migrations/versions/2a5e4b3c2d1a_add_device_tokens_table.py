"""add device_tokens table

Revision ID: 2a5e4b3c2d1a
Revises: 8e44c21a4f0b
Create Date: 2026-04-09 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a5e4b3c2d1a'
down_revision = '8e44c21a4f0b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create device_tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_device_tokens_id'), 'device_tokens', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_device_tokens_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
