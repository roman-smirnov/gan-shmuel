def test_session_by_ID(client, in_truck_payload):
    post_response = client.post("/weight", data=in_truck_payload)
    temp = client.get("/item/TRUCK123")
    session_id = temp.get_json()[0]["session_id"]
    response = client.get(f"/session/{session_id}")
    response_data = response.get_json()
    assert response.status_code == 200
    assert response_data == {'bruto': 2000, 'id': '1', 'truck': 'TRUCK123'}