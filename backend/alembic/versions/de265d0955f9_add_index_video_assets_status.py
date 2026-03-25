"""add index on video_assets.status

Revision ID: de265d0955f9
Revises: 0384ae4e26a2
Create Date: 2026-03-25

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'de265d0955f9'
down_revision: str | None = '0384ae4e26a2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index('ix_video_assets_status', 'video_assets', ['status'])


def downgrade() -> None:
    op.drop_index('ix_video_assets_status', table_name='video_assets')
