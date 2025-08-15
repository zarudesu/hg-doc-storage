"""Create contracts table

Revision ID: 001_initial
Revises: 
Create Date: 2025-08-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contracts table
    op.create_table('contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.Text(), nullable=False),
        sa.Column('contract_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('original_file_path', sa.Text(), nullable=False),
        sa.Column('signed_file_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signer_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_client_id'), 'contracts', ['client_id'], unique=False)
    op.create_index(op.f('ix_contracts_status'), 'contracts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_contracts_status'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_client_id'), table_name='contracts')
    op.drop_table('contracts')
