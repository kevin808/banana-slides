"""add device_id to projects

Revision ID: 007_add_device_id
Revises: 006_add_export_settings
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_device_id'
down_revision = '006_add_export_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add device_id field to projects table for device-based user isolation.
    - device_id: Unique device identifier from client (nullable for backward compatibility)
    """
    # Add device_id column (nullable to support existing projects)
    op.add_column('projects', sa.Column('device_id', sa.String(255), nullable=True))

    # Add index for faster queries
    op.create_index('idx_projects_device_id', 'projects', ['device_id'])


def downgrade() -> None:
    """
    Remove device_id field from projects table.
    """
    op.drop_index('idx_projects_device_id', table_name='projects')
    op.drop_column('projects', 'device_id')
