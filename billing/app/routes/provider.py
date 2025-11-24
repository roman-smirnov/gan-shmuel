from flask import request, jsonify             
from app.models.provider import create_provider, get_provider, get_provider_by_name, update_provider     
from flask import Blueprint  

providers_bp = Blueprint("providers", __name__) 

@providers_bp.route('/provider', methods=['POST']) # Define POST route for creating a new provider
def add_new_provider():
    # Retrieve the JSON payload from the request body

    payload = request.get_json()

    # Validate input: JSON must contain a "name" field
    if not payload or "name" not in payload:
        return jsonify({"error": "You must provide a 'name' field."}), 400

    # Extract the provider name and remove unwanted whitespace (spaces, tabs, newlines)
    provider_name = payload["name"].strip()

    # Reject empty strings (after removing whitespace)
    if not provider_name:
        return jsonify({"error": "Provider name cannot be empty."}), 400

    # Check if a provider with the same name already exists in the database
    existing_provider = get_provider_by_name(provider_name)
    if existing_provider:
        # HTTP 409 = Conflict → record already exists
        return jsonify({"error": "This provider name already exists."}), 409

    # Create a new Provider instance and save it to the database
    provider_id = create_provider(provider_name)

    # Return only the generated provider ID as required — HTTP 201 = Created
    return jsonify({"id": str(provider_id)}), 201


@providers_bp.route('/provider/<int:provider_id>', methods=['PUT']) 
def put_provider(provider_id):
    """
    Update an existing provider's name.
    """
    payload = request.get_json()
    
    # Check if user added a name
    if not payload or 'name' not in payload:
        return jsonify({'error': 'Name is required'}), 400
    
    # Extract input
    name = payload['name']
    
    # Validate input
    if not name or not name.strip():
        return jsonify({'error': 'Name cannot be empty'}), 400
    
    # Check if provider exists
    existing = get_provider(provider_id)
    if not existing:
        return jsonify({'error': 'Provider not found'}), 404
    
    # Check if new name is already used by another provider
    name_stripped = name.strip()
    existing_with_name = get_provider_by_name(name_stripped)
    if existing_with_name and existing_with_name['id'] != provider_id:
        return jsonify({'error': 'Provider with this name already exists'}), 409

    # Check if updating provider name worked
    success = update_provider(provider_id, name_stripped)
    
    if success:
        return jsonify({'id': provider_id, 'name': name_stripped}), 200
    else:
        return jsonify({'error': 'Failed to update provider'}), 500
