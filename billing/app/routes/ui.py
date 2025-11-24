from flask import Blueprint, render_template, request
from app.models.provider import get_all_providers, create_provider

ui_bp = Blueprint("ui", __name__)

@ui_bp.route("/", methods=["GET", "POST"])
def home():
    error_message = None
    success_message = None

    # בשלב הזה כבר נטפל גם ב-POST של providers
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "provider":
            name = request.form.get("name", "").strip()

            if not name:
                error_message = "Provider name is required."
            else:
                try:
                    provider_id = create_provider(name)
                    success_message = f"Provider created with id {provider_id}"
                except Exception:
                    error_message = "Failed to create provider."

    # תמיד נביא את רשימת הספקים
    providers = get_all_providers()

    return render_template(
        "ui.html",
        providers=providers,
        error_message=error_message,
        success_message=success_message,
    )

