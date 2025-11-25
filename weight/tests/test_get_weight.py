def test_get_transactions(client, in_truck_payload, out_truck_payload):
    client.post("/weight", data=in_truck_payload)
    client.post("/weight", data=out_truck_payload) 
    response = client.get("/weight")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
