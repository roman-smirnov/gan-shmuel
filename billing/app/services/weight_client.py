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
    """
    url = current_app.config['WEIGHT_BASE_URL']
    
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
        data = response.json()
        
        
        # FIX: Extract sessions from the response
        if isinstance(data, dict) and 'results' in data:
            sessions = data['results']
        elif isinstance(data, list):
            sessions = data
        elif isinstance(data, dict):
            sessions = [data]
        else:
            raise ValueError(f"Unexpected response format from Weight API")
        
        
        # Step 2: For each session, get truck info from GET /session/<id>
        enriched_sessions = []
        for idx, session in enumerate(sessions):
            
            if not isinstance(session, dict):
                continue
            
            session_id = session.get('id')
            if not session_id:
                continue
            
            
            try:
                session_detail = requests.get(
                    f"{url}/session/{session_id}",
                    timeout=5
                )
                session_detail.raise_for_status()
                detail = session_detail.json()
                
                # Merge the data - truck comes from session detail
                enriched_session = {
                    'id': session.get('id'),
                    'direction': session.get('direction'),
                    'truck': detail.get('truck', 'na'),  # ← From GET /session
                    'bruto': session.get('bruto'),
                    'neto': session.get('neto'),
                    'produce': session.get('produce'),
                    'containers': session.get('containers', [])
                }
                enriched_sessions.append(enriched_session)
                
            except requests.exceptions.HTTPError as e:
                # Skip this session if we can't get truck info
                continue
        
        return enriched_sessions
        
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError("Cannot connect to Weight service")
    except requests.exceptions.Timeout as e:
        raise ConnectionError("Weight service timed out")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Weight service error: {e.response.status_code}")

