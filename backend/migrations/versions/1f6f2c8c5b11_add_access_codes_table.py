"""add access_codes table

Revision ID: 1f6f2c8c5b11
Revises: 016_merge_heads, 017_add_elevenlabs_to_settings, 017_icon_subject_ext
Create Date: 2026-03-09 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f6f2c8c5b11'
down_revision = ('016_merge_heads', '017_add_elevenlabs_to_settings', '017_icon_subject_ext')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'access_codes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code_hash', sa.String(length=64), nullable=False),
        sa.Column('plan_name', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('max_generate_requests', sa.Integer(), nullable=True),
        sa.Column('max_export_requests', sa.Integer(), nullable=True),
        sa.Column('used_generate_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used_export_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('code_hash', name='uq_access_codes_code_hash'),
    )
    op.create_index('ix_access_codes_code_hash', 'access_codes', ['code_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_access_codes_code_hash', table_name='access_codes')
    op.drop_table('access_codes')
