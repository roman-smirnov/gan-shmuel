# test health endpoint
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert b"Service is running" in response.data


# test POST /weight endpoint
def test_basic_post_weight(client, in_truck_payload):
    response = client.post("/weight", data=in_truck_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["truck"] == in_truck_payload["truck"]
    assert data["bruto"] == int(in_truck_payload["weight"])


def test_post_out_without_in(client, out_truck_payload):
    response = client.post("/weight", data=out_truck_payload)
    assert response.status_code == 409


def test_post_in_twice(client, in_truck_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=in_truck_payload)
    assert second_response.status_code == 409


def test_post_complete_direction_in_out(client, in_truck_payload, out_truck_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=out_truck_payload)
    assert second_response.status_code == 200


def test_post_in_update_force(client, in_truck_payload, in_truck_update_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=in_truck_update_payload)
    assert second_response.status_code == 200


def test_post_out_update_force(
    client, in_truck_payload, out_truck_payload, out_truck_update_payload
):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=out_truck_payload)
    assert second_response.status_code == 200
    third_response = client.post("/weight", data=out_truck_update_payload)
    assert third_response.status_code == 200
