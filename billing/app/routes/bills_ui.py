# app/routes/bills_ui.py

from flask import Blueprint, render_template, request
from datetime import datetime

from app.models.provider import get_all_providers, get_provider
from app.services.billing_service import calculate_bill

# Blueprint for Bills UI endpoints
ui_bills_bp = Blueprint("ui_bills_bp", __name__)


def build_api_datetime(date_str, time_str):
    """
    Convert HTML date + time fields to API format.

    Example:
      date_str = "2025-01-01"
      time_str = "12:30"
      → "20250101123000"

    Returns:
      - string "yyyymmddhhmmss" if valid
      - None if parsing fails or values are missing.
    """
    if not date_str or not time_str:
        return None

    try:
        combined = f"{date_str} {time_str}"  # "YYYY-MM-DD HH:MM"
        dt = datetime.strptime(combined, "%Y-%m-%d %H:%M")
        return dt.strftime("%Y%m%d%H%M%S")
    except ValueError:
        return None


@ui_bills_bp.route("/bills-ui", methods=["GET", "POST"])
def bills_home():
    """
    UI page for generating billing reports (similar to GET /bill/<id>?from=&to=).

    Supported action (by form_type):
      - "bill_generate" → generate a bill for a provider in a date range.
    """
    error_message = None
    success_message = None
    bill = None
    from_pretty = None
    to_pretty = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "bill_generate":
            provider_raw = request.form.get("provider_id", "").strip()

            # Date & time fields from HTML (user-friendly)
            from_date_raw = request.form.get("from_date", "").strip()
            from_time_raw = request.form.get("from_time", "").strip()
            to_date_raw = request.form.get("to_date", "").strip()
            to_time_raw = request.form.get("to_time", "").strip()

            # ----- Validate provider id -----
            if not provider_raw:
                error_message = "Provider ID is required."
            else:
                try:
                    provider_id = int(provider_raw)
                except ValueError:
                    error_message = "Provider ID must be an integer."

            # Check provider exists
            if not error_message:
                provider = get_provider(provider_id)
                if not provider:
                    error_message = f"Provider {provider_id} not found."

            # ----- Build from/to timestamps in API format (yyyymmddhhmmss) -----
            from_ts = None
            to_ts = None
            from_dt = None
            to_dt = None

            # Check if user touched any date/time fields
            any_date_time = any([from_date_raw, from_time_raw, to_date_raw, to_time_raw])

            if not error_message and any_date_time:
                now = datetime.now()

                # --- Build "to" timestamp ---
                if to_date_raw or to_time_raw:
                    # If user touched "to" fields
                    if not to_date_raw:
                        error_message = "To date is required when To time is provided."
                    else:
                        # If time missing but date present → default to end of day 23:59
                        if not to_time_raw:
                            to_time_raw = "23:59"
                        to_ts = build_api_datetime(to_date_raw, to_time_raw)
                        if not to_ts:
                            error_message = "Invalid 'To' date/time format."
                else:
                    # User only touched "from" fields → default "to" to now
                    to_ts = now.strftime("%Y%m%d%H%M%S")

                # --- Build "from" timestamp ---
                if not error_message:
                    if from_date_raw or from_time_raw:
                        # If user touched "from" fields
                        if not from_date_raw:
                            error_message = "From date is required when From time is provided."
                        else:
                            # If time missing but date present → default to start of day 00:00
                            if not from_time_raw:
                                from_time_raw = "00:00"
                            from_ts = build_api_datetime(from_date_raw, from_time_raw)
                            if not from_ts:
                                error_message = "Invalid 'From' date/time format."
                    else:
                        # User only set "to" → default from = 1st of current month at 00:00:00
                        first_of_month = now.replace(
                            day=1, hour=0, minute=0, second=0, microsecond=0
                        )
                        from_ts = first_of_month.strftime("%Y%m%d%H%M%S")

                # Final safety check for format
                if not error_message:
                    if not (
                        from_ts
                        and to_ts
                        and len(from_ts) == 14
                        and from_ts.isdigit()
                        and len(to_ts) == 14
                        and to_ts.isdigit()
                    ):
                        error_message = (
                            "Internal error: failed to build valid timestamps for API."
                        )

                # Validate logical order: 'to' >= 'from'
                if not error_message:
                    try:
                        from_dt = datetime.strptime(from_ts, "%Y%m%d%H%M%S")
                        to_dt = datetime.strptime(to_ts, "%Y%m%d%H%M%S")
                        if to_dt < from_dt:
                            error_message = (
                                "'To' date/time cannot be earlier than 'From' date/time."
                            )
                        # from_dt / to_dt now ready for pretty display
                    except ValueError:
                        error_message = "Internal error: invalid timestamps built for API."

            # ----- Call billing service -----
            if not error_message:
                try:
                    if any_date_time:
                        # User provided a custom range → use from_ts/to_ts
                        bill = calculate_bill(provider_id, from_ts, to_ts)
                    else:
                        # No date/time given → let service apply its own defaults
                        bill = calculate_bill(provider_id, None, None)

                    # Build human-readable dates for UI:
                    if bill:
                        # If we already built from_dt/to_dt above, reuse them
                        if from_dt and to_dt:
                            from_pretty = from_dt.strftime("%Y-%m-%d %H:%M")
                            to_pretty = to_dt.strftime("%Y-%m-%d %H:%M")
                        else:
                            # Parse from service's "from" / "to" if needed
                            try:
                                from_dt = datetime.strptime(bill["from"], "%Y%m%d%H%M%S")
                                to_dt = datetime.strptime(bill["to"], "%Y%m%d%H%M%S")
                                from_pretty = from_dt.strftime("%Y-%m-%d %H:%M")
                                to_pretty = to_dt.strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                # Fallback: just show raw strings
                                from_pretty = bill.get("from")
                                to_pretty = bill.get("to")

                    success_message = "Bill generated successfully."

                except ValueError as e:
                    # Invalid dates or provider not found (as raised by service)
                    error_message = str(e)
                    bill = None
                except ConnectionError as e:
                    # Weight service unreachable
                    error_message = f"Weight service unavailable: {str(e)}"
                    bill = None
                except Exception:
                    error_message = "Failed to calculate bill."
                    bill = None

    # Always load providers for the dropdown
    try:
        providers = get_all_providers()
    except Exception:
        providers = []
        if not error_message:
            error_message = "Failed to load providers."

    return render_template(
        "bills.html",
        providers=providers,
        bill=bill,
        from_pretty=from_pretty,
        to_pretty=to_pretty,
        error_message=error_message,
        success_message=success_message,
    )

