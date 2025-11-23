from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.truck import create_truck, update_truck, get_truck, get_truck_sessions
from app.models.provider import get_provider

trucks_bp = Blueprint("trucks", __name__)


@trucks_bp.route("/truck", methods=["POST"])
def register_truck():
    """
    POST /truck
    Body JSON example:
    {
      "id": "12-345-67",
      "provider": 1
    }
    """
    payload = request.get_json() or {}

    # Validate required fields
    if "id" not in payload or "provider" not in payload:
        return (
            jsonify({
                "error": "Missing fields",
                "expected": {"id": "<truck license>", "provider": "<provider id>"}
            }),
            400,
        )

    truck_id = str(payload["id"]).strip()

    # Basic validation
    if not truck_id:
        return jsonify({"error": "Truck id cannot be empty"}), 400

    if len(truck_id) > 10:
        return jsonify({"error": "Truck id must be at most 10 characters"}), 400

    try:
        provider_id = int(str(payload["provider"]).strip())
    except (TypeError, ValueError):
        return jsonify({"error": "Provider must be an integer id"}), 400

    # Check that provider exists
    provider = get_provider(provider_id)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404

    # Check that truck does not already exist
    existing_truck = get_truck(truck_id)
    if existing_truck:
        return jsonify({
            "error": "Truck already exists",
            "message": "To update provider, use PUT /truck/{id}"
        }), 409

    # Create truck
    try:
        create_truck(truck_id, provider_id)
    except Exception as e:
        # Handle database errors (e.g., duplicate key, connection issues)
        return jsonify({"error": "Failed to create truck", "details": str(e)}), 500

    return jsonify({"id": truck_id, "provider": provider_id}), 201


@trucks_bp.route("/truck/<string:truck_id>", methods=["PUT"])
def update_truck_provider(truck_id):
    """
    PUT /truck/{id}
    Body JSON example:
    {
      "provider": 2
    }
    """
    # Validate and clean truck_id from URL
    truck_id = truck_id.strip()
    if not truck_id:
        return jsonify({"error": "Truck id cannot be empty"}), 400
    
    payload = request.get_json() or {}

    if "provider" not in payload:
        return jsonify({"error": "Provider field is required"}), 400

    try:
        provider_id = int(str(payload["provider"]).strip())
    except (TypeError, ValueError):
        return jsonify({"error": "Provider must be an integer id"}), 400

    # Check that truck exists
    existing_truck = get_truck(truck_id)
    if not existing_truck:
        return jsonify({"error": "Truck not found"}), 404

    # Check that provider exists
    provider = get_provider(provider_id)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404

    # Update truck provider
    success = update_truck(truck_id, provider_id)

    if not success:
        return jsonify({"error": "Failed to update truck provider"}), 500

    return jsonify({"id": truck_id, "provider": provider_id}), 200


@trucks_bp.route("/truck/<string:truck_id>", methods=["GET"])
def get_truck_info(truck_id):
    """
    GET /truck/<id>?from=t1&to=t2
    Returns:
    {
      "id": <str>,
      "tara": <int> or "na",
      "sessions": [ <id1>, ... ]
    }

    """

    truck = get_truck(truck_id)
    if not truck:
        return jsonify({"error": "Truck not found"}), 404

    t1 = request.args.get("from")
    t2 = request.args.get("to")

    now = datetime.now()
    if not t2:
        t2 = now.strftime("%Y%m%d%H%M%S")
    if not t1:
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        t1 = first_of_month.strftime("%Y%m%d%H%M%S")

    if not (len(t1) == 14 and t1.isdigit() and len(t2) == 14 and t2.isdigit()):
        return jsonify({"error": "from/to must be in format yyyymmddhhmmss"}), 400

    sessions_info = get_truck_sessions(truck_id, t1, t2)

    result = {
        "id": truck_id,
        "tara": sessions_info["tara"],
        "sessions": sessions_info["session_ids"]
    }

    return jsonify(result), 200
