"""Add short_id field to contracts table

Revision ID: 002_add_short_id
Revises: 001_initial
Create Date: 2025-08-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import string
import random

# revision identifiers, used by Alembic.
revision = '002_add_short_id'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def generate_short_id() -> str:
    """Генерирует короткий уникальный ID (8 символов)"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))


def upgrade() -> None:
    # Добавляем поле short_id
    op.add_column('contracts', sa.Column('short_id', sa.String(12), nullable=True))
    
    # Заполняем существующие записи короткими ID
    connection = op.get_bind()
    
    # Получаем все существующие записи
    result = connection.execute(sa.text("SELECT id FROM contracts"))
    contracts = result.fetchall()
    
    # Генерируем и устанавливаем short_id для каждой записи
    used_short_ids = set()
    for contract in contracts:
        short_id = generate_short_id()
        while short_id in used_short_ids:
            short_id = generate_short_id()
        used_short_ids.add(short_id)
        
        connection.execute(
            sa.text("UPDATE contracts SET short_id = :short_id WHERE id = :id"),
            {"short_id": short_id, "id": contract[0]}
        )
    
    # Делаем поле обязательным и уникальным
    op.alter_column('contracts', 'short_id', nullable=False)
    op.create_unique_constraint('uq_contracts_short_id', 'contracts', ['short_id'])
    op.create_index('ix_contracts_short_id', 'contracts', ['short_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_contracts_short_id', table_name='contracts')
    op.drop_constraint('uq_contracts_short_id', 'contracts', type_='unique')
    op.drop_column('contracts', 'short_id')
