def test_get_index_200(client):
    response = client.get("/")
    assert response.status_code == 200
