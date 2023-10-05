"""
This module has functionality to extend FastAPI with a database client.

To initialize this FastAPI extension, call register_db_client() with an instance
of a FastAPI app and an instance of a DBClient.

Example:
    import src.adapters.db as db
    import src.adapters.db.fastapi_db as fastapi_db

    db_client = db.PostgresDBClient()
    app = fastapi.FastAPI()
    fastapi_db.register_db_client(db_client, app)

Then, in a request handler, specify the DB session as a dependency to get a
new database session that lasts for the duration of the request.

Example:
    import src.adapters.db as db
    import src.adapters.db.fastapi_db as fastapi_db

    @app.get("/health")
    def health(db_session: db.Session = Depends(fastapi_db.DbSessionDependency())):
        with db_session.begin():
            ...

The session can also be defined as an annotation in the typing like:
`db_session: typing.Annotated[db.Session, fastapi.Depends(fastapi_db.DbSessionDependency())]`
if you want to avoid having the function defined with a default value

Alternatively, if you want to get the database client directly, use the get_db_client
function which requires you have the application itself via the Request

Example:
    from fastapi import Request
    import src.adapters.db.fastapi_db as fastapi_db

    @app.get("/health")
    def health(request: Request):
        db_client = fastapi_db.get_db_client(request.app)
        # db_client.get_connection() or db_client.get_session()
"""

from typing import Generator

import fastapi

import src.adapters.db as db

_FASTAPI_KEY_PREFIX = "db"
_DEFAULT_CLIENT_NAME = "default"


def register_db_client(
    db_client: db.DBClient, app: fastapi.FastAPI, client_name: str = _DEFAULT_CLIENT_NAME
) -> None:
    fastapi_state_key = f"{_FASTAPI_KEY_PREFIX}{client_name}"
    setattr(app.state, fastapi_state_key, db_client)


def get_db_client(app: fastapi.FastAPI, client_name: str = _DEFAULT_CLIENT_NAME) -> db.DBClient:
    fastapi_state_key = f"{_FASTAPI_KEY_PREFIX}{client_name}"
    return getattr(app.state, fastapi_state_key)


class DbSessionDependency:
    """
    FastAPI dependency class that can be used to fetch a DB session::

        import src.adapters.db as db
        import src.adapters.db.fastapi_db as fastapi_db

        @app.get("/health")
        def health(db_session: db.Session = Depends(fastapi_db.DbSessionDependency())):
            with db_session.begin():
                ...

    This approach to setting up a dependency allows us to take in a parameter (the client name)
    See: https://fastapi.tiangolo.com/advanced/advanced-dependencies/#a-callable-instance
    """

    def __init__(self, client_name: str = _DEFAULT_CLIENT_NAME):
        self.client_name = client_name

    def __call__(self, request: fastapi.Request) -> Generator[db.Session, None, None]:
        with get_db_client(request.app, self.client_name).get_session() as session:
            yield session
