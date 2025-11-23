import requests
from flask import current_app

def get_item_from_weight(truck_id, from_date, to_date):
    """
    Call Weight service: GET /item/<id>?from=t1&to=t2
    """
    base_url = current_app.config['WEIGHT_BASE_URL']  
    url = f"{base_url}/item/{truck_id}"

    params = {
        "from": from_date,
        "to": to_date
    }

    resp = requests.get(url, params=params, timeout=3)
    resp.raise_for_status()  

    return resp.json()
