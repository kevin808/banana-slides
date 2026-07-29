"""add image quality control setting

Revision ID: b7d8c9e4f2a1
Revises: 021_disable_icon_subject_extraction_default
Create Date: 2026-07-01 10:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'b7d8c9e4f2a1'
down_revision = '021_disable_icon_subject_extraction_default'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {
        column['name']
        for column in sa.inspect(bind).get_columns('settings')
    }
    if 'enable_image_quality_control' not in columns:
        op.add_column(
            'settings',
            sa.Column(
                'enable_image_quality_control',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade():
    op.drop_column('settings', 'enable_image_quality_control')
