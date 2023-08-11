"""default table privileges

Revision ID: 3ed861176e3d
Revises: 
Create Date: 2023-08-10 15:52:10.626153

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "3ed861176e3d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO app")


def downgrade():
    op.execute(f"ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM app")
