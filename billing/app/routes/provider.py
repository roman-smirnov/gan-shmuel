from flask import request, jsonify             
from app.models.provider import create_provider, get_provider_by_name     
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