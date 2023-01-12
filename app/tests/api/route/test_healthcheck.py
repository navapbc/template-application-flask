import api.db


def test_get_healthcheck_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_get_healthcheck_503_db_bad_state(client, monkeypatch):
    # Make fetching the DB session fail
    def err_method(*args):
        raise Exception("Fake Error")

    # Mock api.db.DB.get_session method to fail
    monkeypatch.setattr(api.db.DB, "get_connection", err_method)

    response = client.get("/health")
    assert response.status_code == 503
