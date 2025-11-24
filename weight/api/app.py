from datetime import datetime, timezone
from flask import Flask, Response, request, abort, jsonify

from flask_sqlalchemy import SQLAlchemy
import secrets
import os
import json
import utils

    

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.secret_key = secrets.token_hex(6)
# generate a random 12 characters in hexadecimal for secret key

# Configure the database connection
db_user = os.getenv("MYSQL_USER")
db_pass = os.getenv("MYSQL_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_pass}@weight-db:3306/{db_name}"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


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

# inject dependencies to utils
utils.db = db
utils.Transactions = Transactions
utils.Containers_registered = Containers_registered


# endpoint definitions


@app.route("/health", methods=["GET"])
def health():
    return Response("Service is running", status=200)


@app.route("/weight", methods=["GET"])
def get_weight():
    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    direction = request.args.get("filter")

    # Parse dates if provided
    from_date = utils.str_to_datetime(raw_from) if raw_from else None
    to_date = utils.str_to_datetime(raw_to) if raw_to else None

    relevant_transactions = utils.get_query_transactions(
        from_date, to_date, direction, None, None
    )
    results = []
    for transaction in relevant_transactions:
        results.append(
            {
                "id": transaction.id,
                "direction": transaction.direction,
                "bruto": transaction.bruto,
                "neto": transaction.neto,
                "produce": transaction.produce,
                "containers": transaction.containers,
            }
        )
    return {"results": results}


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
                return utils.verbose(last_row)

            abort(409, description=f"truck already {last_row.direction} use force=True to update")
    elif new_row.direction == "out":
       # handle situation that a truck that isn't in trying to leave
       abort(409, description=f"truck isn't in {new_row.direction} use force=True to update")

    db.session.add(new_row)
    db.session.commit()
    #
    return utils.verbose(new_row)


@app.route("/item/<item_id>", methods=["GET"])
def get_item(item_id):
    raw_from = request.args.get("from")
    raw_to = request.args.get("to")

    # return 404 if item isnt availble
    if len(utils.get_query_transactions(None, None, None, item_id, None)) == 0:
        return Response("Item not found", status=404)

    # handle date range
    if not raw_from:
        from_date = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    else:
        from_date = utils.str_to_datetime(raw_from)
    if not raw_to:
        to_date = datetime.now()
    else:
        to_date = utils.str_to_datetime(raw_to)
    # query transactions by item

    relevent_transactions = utils.get_query_transactions(
        from_date, to_date, None, item_id, None
    )
    results = []
    for transaction in relevent_transactions:
        results.append(
            {
                "id": transaction.id,
                "tara": transaction.truckTara,
                "session_id": transaction.session_id,
            }
        )
    return results


@app.route("/batch-weight", methods=["POST"])
def batch_weight():
    filename = request.args.get("file")
    extension = filename.split(".")[-1]
    match extension:
        case "csv":
            with open(f"in/{filename}", "r") as f:
                lines = f.readlines()
                header = lines[0].strip().split(",")
                unit = header[1]
                for line in lines[1:]:
                    cid, weight = line.strip().split(",")
                    db.session.add(
                        Containers_registered(
                            container_id=cid, weight=weight, unit=unit
                        )
                    )

            db.session.commit()
            return Response("Batch processed successfully", status=200)
        case "json":
            with open(f"in/{filename}", "r") as f:
                data = json.load(f)
            for entry in data:
                cid = entry["id"]
                weight = entry["weight"]
                unit = entry["unit"]
                db.session.add(
                    Containers_registered(container_id=cid, weight=weight, unit=unit)
                )
            db.session.commit()
            return Response("Batch processed successfully", status=200)

        case _:
            return Response("Unsupported file format", status=400)

@app.route("/session/<id>", methods=["GET"])
def get_session(id):
    
    rows = transactions.query.filter(
    transactions.id == id
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

    in_row = rows[0]
    return jsonify({
        "id": str(in_row.id),
        "truck": in_row.truck if in_row.truck else "na",
        "bruto": in_row.bruto
    }), 200

@app.route("/unknown", methods=["GET"])
def unknown():
    result = []
    unknown_containers = (
        db.session.query(Containers_registered.container_id)
        .filter(Containers_registered.weight == "")
        .all()
    )
    for container in unknown_containers:
        result.append(container.container_id)
    if not result:
        return Response(
            "No unknown containers found", status=204, mimetype="text/plain"
        )
    return Response(", ".join(result) + ",", status=200, mimetype="text/plain")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
