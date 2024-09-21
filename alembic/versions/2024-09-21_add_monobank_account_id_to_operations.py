"""add monobank_account_id to operations

Revision ID: ede6c00a28eb
Revises: b404db959827
Create Date: 2024-09-21 00:23:48.353965

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ede6c00a28eb"
down_revision = "b404db959827"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("operations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("monobank_account_id", sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("operations", schema=None) as batch_op:
        batch_op.drop_column("monobank_account_id")

    # ### end Alembic commands ###