import api.app as app


def test_get_healthcheck_200(client):
    response = client.get("/v1/healthcheck")
    assert response.status_code == 200


def test_get_healthcheck_503_db_bad_state(client, monkeypatch):
    # Make fetching the DB session fail
    def err_method(*args):
        raise Exception("Fake Error")

    monkeypatch.setattr(app, "db_session", err_method)

    response = client.get("/v1/healthcheck")
    assert response.status_code == 503
