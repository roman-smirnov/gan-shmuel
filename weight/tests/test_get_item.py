def test_search_by_truck(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    response = client.get("/item/TRUCK123")
    response_data = response.get_json()
    assert response.status_code == 200
    assert response_data[0]["id"] == 1
    assert response_data[0]["tara"] is None
    assert response_data[0]["session_id"] is not None

def test_search_by_container(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    response = client.get("/item/C1")
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]["id"] == 1
    assert data[0]["tara"] is None
    assert data[0]["session_id"] is not None


