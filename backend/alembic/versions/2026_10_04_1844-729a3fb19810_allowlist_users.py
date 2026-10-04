"""allowlist users

Revision ID: 729a3fb19810
Revises: 1024a92c1883
Create Date: 2026-10-04 18:44:13.075128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.models.base


# revision identifiers, used by Alembic.
revision: str = '729a3fb19810'
down_revision: Union[str, Sequence[str], None] = '1024a92c1883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allowlist users (DECISIONS.md 56): status active/disabled, email-only rows, no admin mail."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_users_status'), type_='check')
        batch_op.alter_column('google_sub', existing_type=sa.VARCHAR(length=255), nullable=True)
        batch_op.alter_column('name', existing_type=sa.VARCHAR(length=255), nullable=True)
        batch_op.drop_column('notified_at')

    # Old statuses: approved -> active, pending/rejected -> disabled. Emails are matched lowercase.
    op.execute("UPDATE users SET status = CASE WHEN status = 'approved' THEN 'active' ELSE 'disabled' END")
    op.execute("UPDATE users SET email = lower(email)")

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_users_email'), ['email'])
        batch_op.create_check_constraint(op.f('ck_users_status'), "status IN ('active', 'disabled')")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_users_status'), type_='check')
        batch_op.drop_constraint(batch_op.f('uq_users_email'), type_='unique')

    op.execute("UPDATE users SET status = CASE WHEN status = 'active' THEN 'approved' ELSE 'rejected' END")
    # Rows registered by email only have no Google details yet; they cannot exist in the old shape.
    op.execute("DELETE FROM users WHERE google_sub IS NULL OR name IS NULL")

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notified_at', app.models.base.UTCDateTime(), nullable=True))
        batch_op.alter_column('name', existing_type=sa.VARCHAR(length=255), nullable=False)
        batch_op.alter_column('google_sub', existing_type=sa.VARCHAR(length=255), nullable=False)
        batch_op.create_check_constraint(op.f('ck_users_status'), "status IN ('pending', 'approved', 'rejected')")
