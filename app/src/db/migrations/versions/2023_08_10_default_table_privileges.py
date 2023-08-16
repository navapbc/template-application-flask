"""default table privileges

Revision ID: 3ed861176e3d
Revises:
Create Date: 2023-08-10 15:52:10.626153

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ed861176e3d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Change default privileges for future objects created by the `migrator`
    # user to automatically be accessible by the `app` user.
    op.execute("ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO app")
    op.execute("ALTER DEFAULT PRIVILEGES GRANT ALL ON SEQUENCES TO app")
    op.execute("ALTER DEFAULT PRIVILEGES GRANT ALL ON ROUTINES TO app")


def downgrade():
    op.execute("ALTER DEFAULT PRIVILEGES REVOKE ALL ON ROUTINES FROM app")
    op.execute("ALTER DEFAULT PRIVILEGES REVOKE ALL ON SEQUENCES FROM app")
    op.execute("ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM app")
