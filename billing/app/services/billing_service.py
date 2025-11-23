# =============================================================================
# BILLING SERVICE
# =============================================================================
# Core business logic for calculating provider bills.

from datetime import datetime
from app.models.provider import get_provider
from app.models.truck import get_trucks_by_provider
from app.models.rate import get_rate
from app.services.weight_client import get_weight_data

def calculate_bill(provider_id, from_date=None, to_date=None):
    """
    Calculate the total bill for a provider.
    """
    # Handle default dates
    now = datetime.now()
    
    if not from_date:
        # Default: 1st of current month at 000000
        from_date = now.strftime('%Y%m01000000')
    
    if not to_date:
        # Default: now
        to_date = now.strftime('%Y%m%d%H%M%S')
    
    # Validate date format 
    if len(from_date) != 14 or not from_date.isdigit():
        raise ValueError(f"Invalid from date format: {from_date}. Expected yyyymmddhhmmss")
    
    if len(to_date) != 14 or not to_date.isdigit():
        raise ValueError(f"Invalid to date format: {to_date}. Expected yyyymmddhhmmss")
    
    # Get provider info
    provider = get_provider(provider_id)
    if not provider:
        raise ValueError(f"Provider {provider_id} not found")
    
    # Get all trucks belonging to this provider
    trucks = get_trucks_by_provider(provider_id)
    
    # Fetch all weighing data from Weight service
    # filter='in' gets only incoming (delivery) weights
    weight_data = get_weight_data(from_date, to_date, filter_type='in')
    
    # Filter for this provider's trucks only
    provider_sessions = [
        session for session in weight_data
        if session.get('truck') in trucks
    ]
    
    # Calculate totals per product
    products = {}
    
    for session in provider_sessions:
        produce = session.get('produce', 'Unknown')
        neto = session.get('neto')
        
        # Skip sessions with unavailable weight
        # Weight service returns 'na' if truck hasn't left yet
        if neto == 'na' or neto is None:
            continue
        
        # Convert neto to int if it's a string number
        try:
            neto = int(neto)
        except (ValueError, TypeError):
            continue  # Skip invalid weights
        
        # Initialize product entry if first occurrence
        if produce not in products:
            # Look up rate: provider-specific first, then global
            rate = get_rate(produce, provider_id)
            products[produce] = {
                'count': 0,      # Number of sessions
                'amount': 0,     # Total weight in kg
                'rate': rate     # Price per kg in agorot
            }
        
        products[produce]['count'] += 1
        products[produce]['amount'] += neto
    
    # Build product list with payment calculations
    product_list = []
    total = 0
    
    for produce, data in products.items():
        pay = data['amount'] * data['rate']
        total += pay
        
        product_list.append({
            'product': produce,
            'count': str(data['count']),     # String as per spec
            'amount': data['amount'],         # Int (kg)
            'rate': data['rate'],             # Int (agorot)
            'pay': pay                        # Int (agorot)
        })
    
    return {
        'id': str(provider_id),               # String as per spec
        'name': provider['name'],
        'from': from_date,
        'to': to_date,
        'truckCount': len(trucks),
        'sessionCount': len(provider_sessions),
        'products': product_list,
        'total': total                        # Int (agorot)
    }