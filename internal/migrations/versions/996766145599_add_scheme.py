"""Add scheme

Revision ID: 996766145599
Revises: dc3e0231c0a7
Create Date: 2024-12-21 10:59:16.477341

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "996766145599"
down_revision = "dc3e0231c0a7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("cartogram_entry", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheme", sa.String(length=15), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("cartogram_entry", schema=None) as batch_op:
        batch_op.drop_column("scheme")

    # ### end Alembic commands ###
