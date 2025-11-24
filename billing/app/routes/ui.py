from flask import Blueprint, render_template, request
from app.models.provider import (
    create_provider,
    get_all_providers,
    get_provider_by_name,
    get_provider,       # used for checking if provider exists before update
    update_provider     # used to update the provider's name
)

# Creating the Blueprint for UI routes
ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/", methods=["GET", "POST"])
def home():
    """
    This is the main UI route.
    It handles both GET (show page) and POST (handle forms).
    """

    error_message = None       # Error message to display on the page
    success_message = None     # Success message to display on the page

    # ------------------------
    # If a form was submitted
    # ------------------------
    if request.method == "POST":
        # form_type tells us WHICH form was submitted (create or update)
        form_type = request.form.get("form_type")

        # ====================================================
        #  CREATE PROVIDER FORM  → form_type == "provider"
        # ====================================================
        if form_type == "provider":
            name = request.form.get("name", "").strip()  # get provider name from form

            # Validate input: name cannot be empty
            if not name:
                error_message = "Provider name is required."
            else:
                # Check if the name already exists in DB
                existing = get_provider_by_name(name)
                if existing:
                    error_message = "This provider name already exists."
                else:
                    try:
                        # Create the provider in DB
                        provider_id = create_provider(name)
                        success_message = f"Provider created with id {provider_id}"
                    except Exception:
                        error_message = "Failed to create provider."

        # ====================================================
        #  UPDATE PROVIDER FORM  → form_type == "provider_update"
        # ====================================================
        elif form_type == "provider_update":
            provider_id_raw = request.form.get("provider_id")  # received from <select>
            new_name = request.form.get("name", "").strip()    # new name from form

            # 1) Validate: new name must not be empty
            if not new_name:
                error_message = "New provider name cannot be empty."

            # 2) Validate: provider_id must exist in the form
            elif not provider_id_raw:
                error_message = "Provider id is required for update."

            else:
                # Convert provider_id to int (because form data is a string)
                try:
                    provider_id = int(provider_id_raw)
                except ValueError:
                    error_message = "Provider id must be a number."
                else:
                    # 3) Check if provider exists in DB
                    existing = get_provider(provider_id)
                    if not existing:
                        error_message = "Provider not found."
                    else:
                        # 4) Check if new name is already taken by another provider
                        existing_with_name = get_provider_by_name(new_name)
                        if existing_with_name and existing_with_name["id"] != provider_id:
                            error_message = "Another provider already uses this name."
                        else:
                            # 5) Try to update provider in DB
                            try:
                                success = update_provider(provider_id, new_name)
                                if success:
                                    success_message = f"Provider {provider_id} updated successfully."
                                else:
                                    error_message = "Failed to update provider."
                            except Exception:
                                error_message = "Failed to update provider."

    # ========================================================
    # Always load all providers → for table & for select menu
    # ========================================================
    providers = get_all_providers()

    # Render ui.html and pass data to it (Jinja template)
    return render_template(
        "ui.html",
        providers=providers,
        error_message=error_message,
        success_message=success_message,
    )

