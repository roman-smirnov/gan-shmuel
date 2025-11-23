
from flask import Blueprint, jsonify, request, send_file, current_app
import os
from app.services.rate_parser import parse_rates_file
from app.models.rate import save_rates, get_all_rates

rates_bp = Blueprint("rates", __name__) 

@rates_bp.route("/rates", methods=["POST"])
def post_rates():
    """
    Upload and process a rates file.
    """
    data = request.get_json()
    
    # Validate request has filename
    if not data or 'file' not in data:
        return jsonify({'error': 'file parameter is required'}), 400
    
    filename = data['file']
    
    # Build full path to the file
    filepath = os.path.join('/app/in', filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        return jsonify({'error': f'File {filename} not found in /in folder'}), 404
    
    try:
        # Parse the Excel file
        rates = parse_rates_file(filepath)
        
        # Validate rates
        if not rates:
            return jsonify({'error': 'No rates found in file'}), 400
        
        # Replace all existing instances with the new rates
        save_rates(rates)
        
        return jsonify({
            'status': 'ok',
            'count': len(rates)
        }), 200
        
    except ValueError as e:
        # File format is invalid
        return jsonify({'error': f'Invalid file format: {str(e)}'}), 400
    except Exception as e:
        # Unexpected error
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500