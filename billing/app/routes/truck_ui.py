from flask import Blueprint, render_template, request
from datetime import datetime

from app.models.truck import (
    create_truck,
    update_truck,
    get_truck,
    get_truck_sessions,
)
from app.models.provider import (
    get_all_providers,
    get_provider,
)

# Blueprint for Truck UI endpoints
ui_truck_bp = Blueprint("ui_truck_bp", __name__)


def build_api_datetime(date_str, time_str):
    """
    Convert HTML date + time fields to API format.

    Example:
      date_str = "2025-01-01"
      time_str = "12:30"
      → "20250101123000"

    Returns:
      - string "yyyymmddhhmmss" if valid
      - None if parsing fails or missing values
    """
    if not date_str or not time_str:
        return None

    try:
        combined = f"{date_str} {time_str}"  # "YYYY-MM-DD HH:MM"
        dt = datetime.strptime(combined, "%Y-%m-%d %H:%M")
        return dt.strftime("%Y%m%d%H%M%S")
    except ValueError:
        return None


@ui_truck_bp.route("/truck-ui", methods=["GET", "POST"])
def truck_home():
    """
    Main UI page for managing Trucks.

    Supported actions (by form_type):
      - "truck_create"  → create/register a new truck
      - "truck_update"  → update truck's provider
      - "truck_info"    → fetch tara + sessions for a truck
    """
    error_message = None
    success_message = None
    truck_info = None  # Used to show GET /truck-like information

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # -------------------- CREATE TRUCK (POST /truck) --------------------
        if form_type == "truck_create":
            truck_id_raw = request.form.get("truck_id", "").strip()
            provider_raw = request.form.get("provider_id", "").strip()

            # Validate truck id
            if not truck_id_raw:
                error_message = "Truck ID (license plate) is required."
            elif len(truck_id_raw) > 10:
                error_message = "Truck ID must be at most 10 characters."

            # Validate provider id
            if not error_message:
                if not provider_raw:
                    error_message = "Provider ID is required."
                else:
                    try:
                        provider_id = int(provider_raw)
                    except ValueError:
                        error_message = "Provider ID must be an integer."

            if not error_message:
                # Check that provider exists
                provider = get_provider(provider_id)
                if not provider:
                    error_message = "Provider not found."
                else:
                    # Check that truck does NOT already exist
                    existing_truck = get_truck(truck_id_raw)
                    if existing_truck:
                        error_message = (
                            "Truck already exists. Use the update form to change its provider."
                        )
                    else:
                        # Create the truck
                        try:
                            create_truck(truck_id_raw, provider_id)
                            success_message = (
                                f"Truck '{truck_id_raw}' registered for provider {provider_id}."
                            )
                        except Exception:
                            error_message = "Failed to create truck."

        # -------------------- UPDATE TRUCK PROVIDER (PUT /truck/<id>) --------------------
        elif form_type == "truck_update":
            truck_id_raw = request.form.get("truck_id", "").strip()
            new_provider_raw = request.form.get("provider_id", "").strip()

            # Basic validation for truck id
            if not truck_id_raw:
                error_message = "Truck ID is required."
            elif len(truck_id_raw) > 10:
                error_message = "Truck ID must be at most 10 characters."

            # Basic validation for provider id
            if not error_message:
                if not new_provider_raw:
                    error_message = "Provider ID is required."
                else:
                    try:
                        new_provider_id = int(new_provider_raw)
                    except ValueError:
                        error_message = "Provider ID must be an integer."

            if not error_message:
                # Check that truck exists
                existing_truck = get_truck(truck_id_raw)
                if not existing_truck:
                    error_message = "Truck not found."
                else:
                    # Check that provider exists
                    provider = get_provider(new_provider_id)
                    if not provider:
                        error_message = "Provider not found."
                    else:
                        # Update truck provider
                        try:
                            success = update_truck(truck_id_raw, new_provider_id)
                            if success:
                                success_message = (
                                    f"Truck '{truck_id_raw}' updated to provider {new_provider_id}."
                                )
                            else:
                                error_message = "Failed to update truck provider."
                        except Exception:
                            error_message = "Failed to update truck provider."

        # -------------------- GET TRUCK INFO (GET /truck/<id>?from=&to=) --------------------
        elif form_type == "truck_info":
            truck_id_raw = request.form.get("truck_id", "").strip()

            # Date & time fields from HTML (nice format for user)
            from_date_raw = request.form.get("from_date", "").strip()
            from_time_raw = request.form.get("from_time", "").strip()
            to_date_raw = request.form.get("to_date", "").strip()
            to_time_raw = request.form.get("to_time", "").strip()

            # Validate truck id
            if not truck_id_raw:
                error_message = "Truck ID is required."
            elif len(truck_id_raw) > 10:
                error_message = "Truck ID must be at most 10 characters."

            # Check that truck exists
            if not error_message:
                existing_truck = get_truck(truck_id_raw)
                if not existing_truck:
                    error_message = "Truck not found."

            # Build timestamps for API (yyyymmddhhmmss)
            from_ts = None
            to_ts = None
            from_dt = None
            to_dt = None

            if not error_message:
                now = datetime.now()

                # --- Build "to" timestamp ---
                if to_date_raw or to_time_raw:
                    # If user touched 'to' fields:
                    if not to_date_raw:
                        error_message = "To date is required when To time is provided."
                    else:
                        # If time is missing but date is present → default to end of day 23:59
                        if not to_time_raw:
                            to_time_raw = "23:59"
                        to_ts = build_api_datetime(to_date_raw, to_time_raw)
                        if not to_ts:
                            error_message = "Invalid 'To' date/time format."
                else:
                    # User left 'to' empty → use 'now'
                    to_ts = now.strftime("%Y%m%d%H%M%S")

                # --- Build "from" timestamp ---
                if not error_message:
                    if from_date_raw or from_time_raw:
                        # If user touched 'from' fields:
                        if not from_date_raw:
                            error_message = "From date is required when From time is provided."
                        else:
                            # If time is missing but date is present → default to start of day 00:00
                            if not from_time_raw:
                                from_time_raw = "00:00"
                            from_ts = build_api_datetime(from_date_raw, from_time_raw)
                            if not from_ts:
                                error_message = "Invalid 'From' date/time format."
                    else:
                        # User left 'from' empty → use first of current month at 00:00:00
                        first_of_month = now.replace(
                            day=1, hour=0, minute=0, second=0, microsecond=0
                        )
                        from_ts = first_of_month.strftime("%Y%m%d%H%M%S")

            # Final safety check: correct length and numeric
            if not error_message:
                if not (
                    from_ts
                    and to_ts
                    and len(from_ts) == 14
                    and from_ts.isdigit()
                    and len(to_ts) == 14
                    and to_ts.isdigit()
                ):
                    error_message = "Internal error: failed to build valid timestamps for API."

            # Validate logical order: 'to' must be >= 'from'
            if not error_message:
                try:
                    from_dt = datetime.strptime(from_ts, "%Y%m%d%H%M%S")
                    to_dt = datetime.strptime(to_ts, "%Y%m%d%H%M%S")
                    if to_dt < from_dt:
                        error_message = (
                            "'To' date/time cannot be earlier than 'From' date/time."
                        )
                except ValueError:
                    error_message = "Internal error: invalid timestamps built for API."

            # Call weight service wrapper only if everything is valid
            if not error_message:
                try:
                    sessions_info = get_truck_sessions(truck_id_raw, from_ts, to_ts)

                    # Build nice, human-readable date/time strings for the UI
                    from_pretty = from_dt.strftime("%Y-%m-%d %H:%M") if from_dt else from_ts
                    to_pretty = to_dt.strftime("%Y-%m-%d %H:%M") if to_dt else to_ts

                    truck_info = {
                        "id": truck_id_raw,
                        "from_api": from_ts,   # API format (hidden, for debugging if needed)
                        "to_api": to_ts,
                        "from_pretty": from_pretty,
                        "to_pretty": to_pretty,
                        "tara": sessions_info.get("tara"),
                        "sessions": sessions_info.get("session_ids", []),
                    }
                except Exception:
                    error_message = "Failed to fetch truck sessions."

    # Always load providers for the dropdowns
    try:
        providers = get_all_providers()
    except Exception:
        providers = []
        if not error_message:
            error_message = "Failed to load providers."

    return render_template(
        "truck.html",
        providers=providers,
        error_message=error_message,
        success_message=success_message,
        truck_info=truck_info,
    )

