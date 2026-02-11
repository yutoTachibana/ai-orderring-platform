"""add_subcontracting_tier_fields

Revision ID: c3f8a2d1e5b7
Revises: abeb11174ac4
Create Date: 2026-02-11 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3f8a2d1e5b7'
down_revision: Union[str, None] = 'abeb11174ac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # エンジニアテーブルに雇用形態カラム追加
    employment_type_enum = sa.Enum('proper', 'freelancer', name='employmenttype')
    employment_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'engineers',
        sa.Column('employment_type', employment_type_enum, server_default='proper', nullable=False),
    )

    # 案件テーブルに再委託制限カラム追加
    tier_limit_enum = sa.Enum('proper_only', 'first_tier', 'no_restriction', name='subcontractingtierlimit')
    tier_limit_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'projects',
        sa.Column('subcontracting_tier_limit', tier_limit_enum, nullable=True),
    )

    # マッチング結果テーブルに商流適格フラグ追加
    op.add_column(
        'matching_results',
        sa.Column('tier_eligible', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('matching_results', 'tier_eligible')
    op.drop_column('projects', 'subcontracting_tier_limit')
    op.drop_column('engineers', 'employment_type')

    # Enum型の削除
    sa.Enum(name='subcontractingtierlimit').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='employmenttype').drop(op.get_bind(), checkfirst=True)
