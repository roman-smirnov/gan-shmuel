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


def get_weight_data(from_date, to_date, filter_type='in'):
    """
    Fetch weighing data from Weight service with truck info.
    
    This requires TWO API calls per session:
    1. GET /weight - to get all sessions
    2. GET /session/<id> - to get truck for each session
    """
    url = current_app.config['WEIGHT_SERVICE_URL']
    
    try:
        # Step 1: Get all weighing sessions
        response = requests.get(
            f"{url}/weight",
            params={
                'from': from_date,
                'to': to_date,
                'filter': filter_type
            },
            timeout=10
        )
        response.raise_for_status()
        sessions = response.json()
        
        # Step 2: For each session, get truck info
        enriched_sessions = []
        for session in sessions:
            session_id = session.get('id')
            
            # Call GET /session/<id> to get truck
            session_detail = requests.get(
                f"{url}/session/{session_id}",
                timeout=5
            )
            session_detail.raise_for_status()
            detail = session_detail.json()
            
            # Merge the data
            enriched_session = {
                'id': session.get('id'),
                'direction': session.get('direction'),
                'truck': detail.get('truck', 'na'),  # ← Get truck from session detail!
                'bruto': session.get('bruto'),
                'neto': session.get('neto'),
                'produce': session.get('produce'),
                'containers': session.get('containers', [])
            }
            enriched_sessions.append(enriched_session)
        
        return enriched_sessions
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to Weight service")
    except requests.exceptions.Timeout:
        raise ConnectionError("Weight service timed out")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Weight service error: {e.response.status_code}")


