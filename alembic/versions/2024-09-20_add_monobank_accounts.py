"""add monobank_accounts

Revision ID: af452ea528bd
Revises: 5b469522b1db
Create Date: 2024-09-20 21:37:34.775280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "af452ea528bd"
down_revision = "5b469522b1db"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "monobank_accounts",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["users.chat_id"],
            name=op.f("fk_monobank_accounts_chat_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_monobank_accounts_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", "chat_id", "company_id", name=op.f("pk_monobank_accounts")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("monobank_accounts")
    # ### end Alembic commands ###