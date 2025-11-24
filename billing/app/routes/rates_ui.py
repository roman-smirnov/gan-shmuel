# app/routes/ui_rates.py

from flask import Blueprint, render_template, request
from app.models.rate import (
    get_all_rates,
    create_rate,      # you must implement in models/rate.py
    update_rate       # you must implement in models/rate.py
)

# Create a Blueprint for Rates UI
ui_rates_bp = Blueprint("ui_rates", __name__)

@ui_rates_bp.route("/rates-ui", methods=["GET", "POST"])
def rates_home():
    """
    UI page for managing Rates.
    This page DOES NOT use Excel.
    It talks directly to models/rate.py (DB access).
    """

    error_message = None
    success_message = None

    # --- Handle form submission ---
    if request.method == "POST":
        form_type = request.form.get("form_type")

        # -------------------------
        # CREATE a new Rate
        # -------------------------
        if form_type == "rate_create":
            product_id_raw = request.form.get("product_id", "").strip()
            rate_raw = request.form.get("rate", "").strip()
            scope = request.form.get("scope", "").strip()

            # Basic validation
            if not product_id_raw:
                error_message = "Product ID is required."
            elif not rate_raw:
                error_message = "Rate value is required."
            elif not scope:
                error_message = "Scope is required."
            else:
                try:
                    rate_value = int(rate_raw)
                except ValueError:
                    error_message = "Rate must be an integer."
                else:
                    # If validation passed → insert into DB
                    try:
                        new_id = create_rate(product_id_raw, rate_value, scope)
                        success_message = f"Rate created successfully with id {new_id}."
                    except Exception:
                        error_message = "Failed to create rate."

        # -------------------------
        # UPDATE an existing rate
        # -------------------------
        elif form_type == "rate_update":
            rate_id_raw = request.form.get("rate_id", "").strip()
            product_id_raw = request.form.get("product_id", "").strip()
            rate_raw = request.form.get("rate", "").strip()
            scope = request.form.get("scope", "").strip()

            if not rate_id_raw:
                error_message = "Rate ID is required for update."
            else:
                try:
                    rate_id = int(rate_id_raw)
                except ValueError:
                    error_message = "Rate ID must be a number."
                else:
                    try:
                        rate_value = int(rate_raw)
                        success = update_rate(rate_id, product_id_raw, rate_value, scope)
                        if success:
                            success_message = f"Rate {rate_id} updated successfully."
                        else:
                            error_message = "Failed to update rate."
                    except Exception:
                        error_message = "Failed to update rate."

    # --- Load all rates for the table ---
    try:
        rates = get_all_rates()
    except Exception:
        rates = []
        if not error_message:
            error_message = "Failed to load rates."

    # --- Render rates.html template ---
    return render_template(
        "rates.html",           # create this next
        rates=rates,
        error_message=error_message,
        success_message=success_message,
    )

