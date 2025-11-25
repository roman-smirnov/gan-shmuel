# routes/rates_ui.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests  # כדי לקרוא ל-POST /rates אחרי שמירת קובץ

ui_rates_bp = Blueprint("ui_rates_bp", __name__)


@ui_rates_bp.route("/rates-ui", methods=["GET", "POST"])
def rates_home():
    error_message = None
    success_message = None

    if request.method == "POST":
        uploaded_file = request.files.get("rates_file")

        if not uploaded_file:
            error_message = "Please select a file."
        else:
            # Save file into /app/in
            save_path = os.path.join("/app", "in", uploaded_file.filename)
            try:
                uploaded_file.save(save_path)
                # Now call the API POST /rates with JSON {"file": filename}
                api_response = requests.post("http://billing-app:5000/rates", json={"file": uploaded_file.filename})
                
                if api_response.status_code == 200:
                    success_message = "Rates uploaded & saved to DB successfully!"
                else:
                    error_message = f"API Error: {api_response.text}"

            except Exception as e:
                error_message = "Failed to save file."

    return render_template(
        "rates.html",
        error_message=error_message,
        success_message=success_message
    )


