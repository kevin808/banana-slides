"""merge device_id and settings heads

Revision ID: 016_merge_heads
Revises: 007_add_device_id, 9ad736fec43d
Create Date: 2026-03-08 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '016_merge_heads'
down_revision = ('007_add_device_id', '9ad736fec43d')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
