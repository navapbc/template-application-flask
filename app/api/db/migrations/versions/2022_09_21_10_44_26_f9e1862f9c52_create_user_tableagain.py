"""Create user tableagain

Revision ID: f9e1862f9c52
Revises: e0563b34f6a6
Create Date: 2022-09-21 10:44:26.134012

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f9e1862f9c52"
down_revision = "e0563b34f6a6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column(
            "another", sa.Enum("USER", "ADMIN", "THIRD_PARTY", name="roleenum"), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "another")
    # ### end Alembic commands ###
