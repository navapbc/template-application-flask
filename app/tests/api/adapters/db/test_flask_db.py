from flask import Flask, current_app
from sqlalchemy import text

import api.adapters.db as db
import api.adapters.db.flask_db as flask_db


def test_get_db(app: Flask):
    @app.route("/hello")
    def hello():
        with flask_db.get_db(current_app).get_connection() as conn:
            return {"data": conn.scalar(text("SELECT 'hello, world'"))}

    response = app.test_client().get("/hello")
    assert response.get_json() == {"data": "hello, world"}


def test_with_db_client(app: Flask):
    @app.route("/hello")
    @flask_db.with_db_client
    def hello(db_client: db.DBClient):
        with db_client.get_connection() as conn:
            return {"data": conn.scalar(text("SELECT 'hello, world'"))}

    response = app.test_client().get("/hello")
    assert response.get_json() == {"data": "hello, world"}


def test_with_db_session(app: Flask):
    @app.route("/hello")
    @flask_db.with_db_session
    def hello(db_session: db.Session):
        with db_session.begin():
            return {"data": db_session.scalar(text("SELECT 'hello, world'"))}

    response = app.test_client().get("/hello")
    assert response.get_json() == {"data": "hello, world"}
