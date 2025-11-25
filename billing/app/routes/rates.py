from flask import Blueprint, jsonify, request, send_file, current_app
import os
from app.services.rate_parser import parse_rates_file
from app.models.rate import save_rates, get_all_rates
from openpyxl import Workbook

rates_bp = Blueprint("rates", __name__)


@rates_bp.route("/rates", methods=["POST"])
def post_rates():
    """
    Upload and process a rates file.
    """
    data = request.get_json()

    # Validate request has filename
    if not data or "file" not in data:
        return jsonify({"error": "file parameter is required"}), 400

    filename = data["file"]

    # Build full path to the file
    filepath = os.path.join("/app/in", filename)

    # Check if file exists
    if not os.path.exists(filepath):
        return jsonify({"error": f"File {filename} not found in /in folder"}), 404

    try:
        # Just to be safe, ensure file is readable/writable by all
        try:
            os.chmod(filepath, 0o666)
        except OSError:
            # If chmod fails, we still try to proceed – not critical for parsing
            pass

        # Parse the Excel file
        rates = parse_rates_file(filepath)

        # Validate rates
        if not rates:
            return jsonify({"error": "No rates found in file"}), 400

        # Replace all existing instances with the new rates
        save_rates(rates)

        return jsonify(
            {
                "status": "ok",
                "count": len(rates),
            }
        ), 200

    except ValueError as e:
        # File format is invalid
        return jsonify({"error": f"Invalid file format: {str(e)}"}), 400
    except Exception as e:
        # Unexpected error
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@rates_bp.get("/rates")  # GET /rates
def get_rates():
    """
    GET /rates
    1. Fetch all rates from the database
    2. If DB is empty → return 404
    3. Otherwise: generate an Excel (.xlsx) file under /app/in
    4. Return the Excel file for download
    """

    # 1) Try to fetch data from DB
    try:
        rates = get_all_rates()
    except Exception:
        current_app.logger.exception("Failed to fetch rates from database")
        return jsonify({"error": "Failed to load rates from database"}), 500

    # 2) Handle case: no rates in DB
    if not rates:
        return (
            jsonify(
                {
                    "error": "No rates found in the database.",
                    "message": "Please upload rates first using POST /rates.",
                }
            ),
            404,
        )

    # 3) Build a safe file path for the Excel file
    file_path = os.path.join("/app", "in", "rates.xlsx")

    # Make sure the directory exists (extra safety)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 4) Generate the Excel file
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Rates"

        # Header row – match the upload format (nice headers)
        headers = ["Product", "Rate", "Scope"]
        ws.append(headers)

        # Data rows from DB
        for row in rates:
            ws.append([row["product_id"], row["rate"], row["scope"]])

        # Save the workbook to disk
        wb.save(file_path)

        # Ensure the file is editable by all (rw-rw-rw-)
        try:
            os.chmod(file_path, 0o666)
        except OSError:
            # If chmod fails, we still allow download
            current_app.logger.warning("Failed to chmod rates.xlsx to 666")

    except Exception:
        current_app.logger.exception("Failed to generate Excel file for rates")
        return jsonify({"error": "Failed to generate Excel file"}), 500

    # 5) Return the Excel file as a download to the client
    return send_file(
        file_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="rates.xlsx",
    )

