from flask import Blueprint, render_template, request
from app.models.provider import create_provider, get_all_providers, get_provider_by_name

@ui_bp.route("/", methods=["GET", "POST"])
def home():
    error_message = None
    success_message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "provider":
            name = request.form.get("name", "").strip()

            if not name:
                error_message = "Provider name is required."
            else:
                #check if name already exixt;
                existing = get_provider_by_name(name)
                if existing:
                    error_message = "This provider name already exists."
                else:
                    try:
                        provider_id = create_provider(name)
                        success_message = f"Provider created with id {provider_id}"
                    except Exception:
                        error_message = "Failed to create provider."

    # We will always re-fetch the list of providers:
    providers = get_all_providers()

    return render_template(
        "ui.html",
        providers=providers,
        error_message=error_message,
        success_message=success_message,
    )
