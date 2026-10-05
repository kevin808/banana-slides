"""Merge local migration history with upstream image-quality migrations."""

revision = '023_merge_upstream_image_quality_head'
down_revision = ('022_merge_upstream_quality_control_head', 'c42f8e9a1b70')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
