"""merge upstream quality-control migration head

Revision ID: 022_merge_upstream_quality_control_head
Revises: 021_disable_icon_subject_extraction_default, 78475bbce762
Create Date: 2026-07-29 00:00:00.000000

"""

revision = '022_merge_upstream_quality_control_head'
down_revision = (
    '021_disable_icon_subject_extraction_default',
    '78475bbce762',
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
