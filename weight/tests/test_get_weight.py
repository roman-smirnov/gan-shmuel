from datetime import datetime, timedelta


def test_get_transactions(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    response = client.get("/weight")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1


def test_get_transaction_by_direction_in(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    response = client.get("/weight", query_string={"filter": "in"})
    assert response.status_code == 200
    data = response.get_json()
    [actual] = data["results"]
    expected = {
        "id": 1,
        "direction": "in",
        "bruto": 2000,
        "neto": None,
        "produce": "apples",
        "containers": "C1,C2",
    }
    assert actual == expected


def test_get_transaction_by_direction_out_bruto_neto(
    client, truck_no_containers_payload_in, truck_no_containers_payload_out
):
    first_response = client.post("/weight", data=truck_no_containers_payload_in)
    second_response = client.post("/weight", data=truck_no_containers_payload_out)
    response = client.get("/weight", query_string={"filter": "out"})
    assert response.status_code == 200
    data = response.get_json()
    [actual] = data["results"]
    expected = {
        "id": 2,
        "direction": "out",
        "bruto": 800,
        "neto": 700,
        "produce": "apples",
        "containers": "",
    }
    assert actual == expected


def test_get_transaction_yesterday(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    yesterday = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        - timedelta(days=1)
    ).strftime("%Y%m%d%H%M%S")
    response = client.get("/weight", query_string={"from": yesterday, "to": yesterday})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) == 0


def test_get_transaction_today(client, in_truck_payload):
    client.post("/weight", data=in_truck_payload)
    start_of_the_day = (
        datetime.now()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .strftime("%Y%m%d%H%M%S")
    )
    end_of_the_day = (
        datetime.now()
        .replace(hour=23, minute=59, second=59, microsecond=999999)
        .strftime("%Y%m%d%H%M%S")
    )
    response = client.get(
        "/weight", query_string={"from": start_of_the_day, "to": end_of_the_day}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) == 1
