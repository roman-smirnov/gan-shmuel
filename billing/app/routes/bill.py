# =============================================================================
# BILLING ENDPOINT
# =============================================================================
# GET /bill/<id> - Generate billing report for a provider

from flask import Blueprint, jsonify, request
from app.models.provider import get_provider
from app.services.billing_service import calculate_bill

bp = Blueprint('bills', __name__)

@bp.route('/bill/<int:provider_id>', methods=['GET'])
def get_bill(provider_id):
    """
    Generate a billing report for a provider.
    
    URL params:
        provider_id: The provider's ID
    
    Returns:
        {
            "id": "10001",
            "name": "Fresh Farms",
            "from": "20240101000000",
            "to": "20240131235959",
            "truckCount": 2,
            "sessionCount": 5,
            "products": [
                {
                    "product": "Navel",
                    "count": "3",
                    "amount": 15000,
                    "rate": 93,
                    "pay": 1395000
                }
            ],
            "total": 1395000
        }
    """
    # Verify provider exists
    provider = get_provider(provider_id)
    if not provider:
        return jsonify({'error': f'Provider {provider_id} not found'}), 404
    
    # Get date range from query params (optional)
    from_date = request.args.get('from')  # None if not provided
    to_date = request.args.get('to')      # None if not provided
    
    try:
        # Calculate the bill
        bill = calculate_bill(provider_id, from_date, to_date)
        return jsonify(bill), 200
        
    except ValueError as e:
        # Invalid date format or provider not found
        return jsonify({'error': str(e)}), 400
    except ConnectionError as e:
        # Weight service is unreachable
        return jsonify({'error': f'Weight service unavailable: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Failed to calculate bill: {str(e)}'}), 500