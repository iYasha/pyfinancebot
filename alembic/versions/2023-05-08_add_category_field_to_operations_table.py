"""add category field to operations table

Revision ID: e21d0fa15ff1
Revises: 54f01b19fa0d
Create Date: 2023-05-08 15:54:28.227655

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e21d0fa15ff1'
down_revision = '54f01b19fa0d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operations', sa.Column('category', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('operations', 'category')
    # ### end Alembic commands ###
