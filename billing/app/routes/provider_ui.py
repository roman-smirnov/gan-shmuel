from flask import Blueprint, render_template, request
from app.models.provider import (
    create_provider,
    get_all_providers,
    get_provider_by_name,
    get_provider,
    update_provider
)

ui_provider_bp = Blueprint("ui_provider_bp", __name__)


@ui_provider_bp.route("/provider-ui", methods=["GET", "POST"])
def provider_home():
    error_message = None
    success_message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --------- CREATE PROVIDER ----------
        # HTML sends: form_type = "provider"
        if form_type == "provider":
            name = request.form.get("name", "").strip()

            if not name:
                error_message = "Provider name is required."
            else:
                existing = get_provider_by_name(name)
                if existing:
                    error_message = "This provider name already exists."
                else:
                    try:
                        provider_id = create_provider(name)
                        success_message = f"Provider created with id {provider_id}"
                    except Exception:
                        error_message = "Failed to create provider."

        # --------- UPDATE PROVIDER ----------
        elif form_type == "provider_update":
            provider_id_raw = request.form.get("provider_id")
            new_name = request.form.get("name", "").strip()

            if not new_name:
                error_message = "New provider name cannot be empty."
            elif not provider_id_raw:
                error_message = "Provider id is required."
            else:
                try:
                    provider_id = int(provider_id_raw)
                except ValueError:
                    error_message = "Provider id must be a number."
                else:
                    existing = get_provider(provider_id)
                    if not existing:
                        error_message = "Provider not found."
                    else:
                        existing_with_name = get_provider_by_name(new_name)
                        if existing_with_name and existing_with_name["id"] != provider_id:
                            error_message = "Another provider already uses this name."
                        else:
                            try:
                                success = update_provider(provider_id, new_name)
                                success_message = (
                                    "Provider updated."
                                    if success else "Failed to update provider."
                                )
                            except Exception:
                                error_message = "Failed to update provider."

    providers = get_all_providers()

    return render_template(
        "ui.html",
        providers=providers,
        error_message=error_message,
        success_message=success_message,
    )

