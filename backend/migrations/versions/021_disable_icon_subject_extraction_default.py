"""disable icon subject extraction by default

Revision ID: 021_disable_icon_subject_extraction_default
Revises: 020_merge_access_codes_and_per_page_template_heads
Create Date: 2026-07-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '021_disable_icon_subject_extraction_default'
down_revision = '020_merge_access_codes_and_per_page_template_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column(
            'enable_icon_subject_extraction',
            existing_type=sa.Boolean(),
            nullable=True,
            server_default=sa.false(),
        )

    op.execute(
        "UPDATE projects "
        "SET enable_icon_subject_extraction = false "
        "WHERE enable_icon_subject_extraction IS NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column(
            'enable_icon_subject_extraction',
            existing_type=sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        )
