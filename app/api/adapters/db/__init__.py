"""
Database module.

Usage:
    import api.adapters.db as db

    db_client = db.init()

    # non-ORM style usage
    with db_client.get_connection() as conn:
        conn.execute(...)

    # ORM style usage
    with db_client.get_session() as session:
        session.query(...)
        with session.begin():
            session.add(...)
"""

# Re-export for convenience
from api.adapters.db.client import Connection, DBClient, Session, init

__all__ = ["Connection", "DBClient", "Session", "init"]
