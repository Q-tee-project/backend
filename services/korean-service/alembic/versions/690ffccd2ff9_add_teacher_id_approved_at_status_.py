"""Add teacher_id approved_at status columns to grading_sessions

Revision ID: 690ffccd2ff9
Revises: 697de91c2aac
Create Date: 2025-09-22 05:43:01.363534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '690ffccd2ff9'
down_revision = '697de91c2aac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add teacher_id column
    op.add_column('grading_sessions',
                  sa.Column('teacher_id', sa.Integer(), nullable=True),
                  schema='korean_service')

    # Add approved_at column
    op.add_column('grading_sessions',
                  sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
                  schema='korean_service')

    # Add status column with default value
    op.add_column('grading_sessions',
                  sa.Column('status', sa.String(), nullable=False, server_default='pending_approval'),
                  schema='korean_service')


def downgrade() -> None:
    # Remove status column
    op.drop_column('grading_sessions', 'status', schema='korean_service')

    # Remove approved_at column
    op.drop_column('grading_sessions', 'approved_at', schema='korean_service')

    # Remove teacher_id column
    op.drop_column('grading_sessions', 'teacher_id', schema='korean_service')