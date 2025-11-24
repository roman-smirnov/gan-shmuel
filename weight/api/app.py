from datetime import datetime, timezone
from flask import Flask, Response, request, render_template, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import utils  # or import utils

db = SQLAlchemy()

def init_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(6)

    if test_config:
        # Use test config (e.g., SQLite in-memory)
        app.config.update(test_config)
    else:
        # Normal production config (MySQL)
        db_user = os.getenv("MYSQL_USER")
        db_pass = os.getenv("MYSQL_PASSWORD")
        db_name = os.getenv("MYSQL_DATABASE")
        db_port = os.getenv("WEIGHT_MYSQL_PORT")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{db_user}:{db_pass}@weight-db:{db_port}/{db_name}"
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Bind db to this app
    db.init_app(app)


    utils.db = db
    utils.Transactions = Transactions
    utils.Containers_registered = Containers_registered

    @app.route("/health", methods=["GET"])
    def health():
        return Response("Service is running", status=200)

    @app.route("/weight", methods=["GET"])
    def get_weight():
        raw_from = request.args.get("from")
        raw_to = request.args.get("to")
        direction = request.args.get("filter")

        from_date = utils.str_to_datetime(raw_from) if raw_from else None
        to_date = utils.str_to_datetime(raw_to) if raw_to else None

        relevant_transactions = utils.get_query_transactions(
            from_date, to_date, direction, None, None
        )

        if is_ui_mode():
            return render_template("weight_search.html", results=relevant_transactions)

        # API mode - convert to dict
        return {
            "results": [
                {
                    "id": t.id,
                    "direction": t.direction,
                    "bruto": t.bruto,
                    "neto": t.neto,
                    "produce": t.produce,
                    "containers": t.containers,
                }
                for t in relevant_transactions
            ]
        }

    @app.route("/weight", methods=["POST"])
    def post_weight():
        data = request.form.to_dict()
        # last_row = Transactions.query.order_by(Transactions.id.desc()).first()
        last_row = None
        rows = utils.get_query_transactions(
            None, None, None, None, data["truck"]
        )  # get the last transaction of the truck
        if rows:
            last_row = rows[-1]

        new_row = Transactions()
        new_row.produce = data.get("produce")
        new_row.direction = data.get("direction")
        new_row.truck = data.get("truck")
        new_row.containers = data.get("containers")
        new_row.truckTara = None
        new_row.neto = None
        force = data.get("force")
        unit = data.get("unit")
        if unit == "kg":
            new_row.bruto = int(data.get("weight"))
        else:
            new_row.bruto = utils.convert_lbs_to_kg(data.get("weight"))

        utils.handle_session(new_row, new_row.direction, data["truck"])  # handle the sessions
        if last_row:  # check if the last row exist

            if last_row.direction == "in" and new_row.direction == "out":
                # handle the situation truck -> in -> out
                containers_weight = utils.calc_containers_weight(new_row.containers)
                if containers_weight or len(new_row.containers) == 0:
                    new_row.truckTara = new_row.bruto - utils.calc_containers_weight(
                        new_row.containers
                    )
                    neto = utils.calc_neto_fruit(
                        int(last_row.bruto), new_row.truckTara, new_row.containers
                    )
                    new_row.neto = neto

            if (last_row.direction == new_row.direction
                    or {last_row.direction, new_row.direction} == {None, "in"}):
                # handles situation that new_record conflicts with old, truck is in and tries to enter again
                if force == "True":
                    utils.update_row(last_row, new_row)
                    if is_ui_mode():
                        return render_template("weight_new.html", result=utils.verbose(last_row))
                    return utils.verbose(last_row)

                abort(409, description=f"truck already {last_row.direction} use force=True to update")
        elif new_row.direction == "out":
            # handle situation that a truck that isn't in trying to leave
            abort(409, description=f"truck isn't in {new_row.direction} use force=True to update")

        db.session.add(new_row)
        db.session.commit()

        # UI mode (form from weight_new.html)
        if is_ui_mode():
            return render_template("weight_new.html", result=utils.verbose(new_row))

        return utils.verbose(new_row)

    @app.route("/item/<item_id>", methods=["GET"])
    def get_item(item_id):
        raw_from = request.args.get("from")
        raw_to = request.args.get("to")

        # Check if item exists
        if not utils.get_query_transactions(None, None, None, item_id, None):
            if is_ui_mode():
                return render_template(
                    "item.html",
                    results=None,
                    error="Item not found",
                    item_id=item_id,
                    raw_from=raw_from or "",
                    raw_to=raw_to or "",
                )
            return Response("Item not found", status=404)

        # Set date range
        from_date = (
            utils.str_to_datetime(raw_from)
            if raw_from
            else datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
        to_date = utils.str_to_datetime(raw_to) if raw_to else datetime.now()

        relevant_transactions = utils.get_query_transactions(
            from_date, to_date, None, item_id, None
        )

        # Build results with appropriate key names
        tara_key = "truckTara" if is_ui_mode() else "tara"
        results = [
            {"id": t.id, tara_key: t.truckTara, "session_id": t.session_id}
            for t in relevant_transactions
        ]

        if is_ui_mode():
            return render_template(
                "item.html",
                results=results,
                error=None,
                item_id=item_id,
                raw_from=raw_from or "",
                raw_to=raw_to or "",
            )

        return results

    @app.route("/batch-weight", methods=["POST"])
    def batch_weight():
        filename = request.args.get("file")
        extension = filename.split(".")[-1]

        def process_csv():
            with open(f"in/{filename}", "r") as f:
                lines = f.readlines()
                unit = lines[0].strip().split(",")[1]
                for line in lines[1:]:
                    cid, weight = line.strip().split(",")
                    db.session.add(
                        Containers_registered(container_id=cid, weight=weight, unit=unit)
                    )

        def process_json():
            with open(f"in/{filename}", "r") as f:
                data = json.load(f)
            for entry in data:
                db.session.add(
                    Containers_registered(
                        container_id=entry["id"], weight=entry["weight"], unit=entry["unit"]
                    )
                )

        processors = {"csv": process_csv, "json": process_json}

        if extension not in processors:
            return Response("Unsupported file format", status=400)

        processors[extension]()
        db.session.commit()
        return Response("Batch processed successfully", status=200)

    # UI routes
    @app.route("/", methods=["GET"])
    def home():
        return render_template("home.html")

    @app.route("/ui/weight/new", methods=["GET"])
    def ui_weight_new():
        return render_template("weight_new.html", result=None)

    @app.route("/ui/item", methods=["GET"])
    def ui_item():
        return render_template(
            "item.html",
            results=None,
            error=None,
            item_id="",
            raw_from="",
            raw_to="",
        )

    @app.route("/session/<id>", methods=["GET"])
    def get_session(id):

        rows = Transactions.query.filter(
            Transactions.id == id
        ).all()

        if not rows:
            return jsonify({"error": "session not found"}), 404

        out_row = next((r for r in rows if r.direction == "out"), None)

        if out_row:
            return jsonify({
                "id": str(out_row.id),
                "truck": out_row.truck if out_row.truck else "na",
                "bruto": out_row.bruto,
                "truckTara": out_row.truckTara if out_row.truckTara is not None else "na",
                "neto": out_row.neto if out_row.neto is not None else "na"
            }), 200
        else:
            in_row = rows[0]
            result = {
                "id": str(in_row.id),
                "truck": in_row.truck if in_row.truck else "na",
                "bruto": in_row.bruto
            }

        if is_ui_mode():
            return render_template("session_details.html", session=out_row or rows[0], error=None)

        return jsonify(result), 200

    @app.route("/ui/session", methods=["GET"])
    def weighting_session():
        session_id = request.args.get("session_id")
        truck = request.args.get("truck")

        sessions = None

        if session_id:
            # Search by session ID
            sessions = Transactions.query.filter(Transactions.session_id == session_id).all()
        elif truck:
            # Search by truck
            sessions = Transactions.query.filter(Transactions.truck == truck).order_by(
                Transactions.datetime.desc()).all()

        return render_template("session.html", sessions=sessions)


    @app.route("/unknown", methods=["GET"])
    def unknown():
        unknown_containers = [
            c.container_id
            for c in db.session.query(Containers_registered.container_id)
            .filter(Containers_registered.weight.in_([0, ""]))
            .all()
        ]
        if is_ui_mode():
            return render_template("unknown.html", containers=unknown_containers)

        # API mode
        if not unknown_containers:
            return Response(
                "No unknown containers found", status=204, mimetype="text/plain"
            )

        return Response(
            ", ".join(unknown_containers) + ",", status=200, mimetype="text/plain"
        )
    return app

# Initialize Flask app and SQLAlchemy
# generate a random 12 characters in hexadecimal for secret key

# Configure the database connection

def is_ui_mode():
    return request.args.get("ui") == "1" or request.form.get("ui") == "1"

# Define database models
class Transactions(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    direction = db.Column(db.String(10))  # in / out / out
    truck = db.Column(db.String(50))
    containers = db.Column(db.String(10000))
    bruto = db.Column(db.Integer)
    truckTara = db.Column(db.Integer)
    neto = db.Column(db.Integer)
    produce = db.Column(db.String(50))
    session_id = db.Column(db.Integer)


class Containers_registered(db.Model):
    __tablename__ = "containers_registered"

    container_id = db.Column(db.String(15), primary_key=True)
    weight = db.Column(db.Integer)
    unit = db.Column(db.String(10))


# Helper function



# endpoint definitions


if __name__ == "__main__":
    app = init_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
