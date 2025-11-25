# routes/rates_ui.py

import os
from flask import Blueprint, render_template, request
import requests

ui_rates_bp = Blueprint("ui_rates_bp", __name__)


@ui_rates_bp.route("/rates-ui", methods=["GET", "POST"])
def rates_home():
    error_message = None
    success_message = None

    if request.method == "POST":
        uploaded_file = request.files.get("rates_file")

        # Validate that a file was actually selected
        if not uploaded_file or uploaded_file.filename == "":
            error_message = "Please select a file."
        else:
            save_path = os.path.join("/app", "in", uploaded_file.filename)

            try:
                uploaded_file.save(save_path)

                # Call the API POST /rates
                api_response = requests.post(
                    "http://billing-app:5000/rates",
                    json={"file": uploaded_file.filename},
                )

                if api_response.status_code == 200:
                    success_message = "Rates uploaded & saved to DB successfully!"
                else:
                    #  ALWAYS show a clean error message – never show the full API JSON
                    error_message = "Failed to process rates file. Please check the format."

            except Exception:
                error_message = "Failed to save file."

    return render_template(
        "rates.html",
        error_message=error_message,
        success_message=success_message
    )

