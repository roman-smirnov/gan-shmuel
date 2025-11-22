from datetime import datetime, timezone
from flask import Flask, Response, request, session
from flask_sqlalchemy import SQLAlchemy
import secrets
import os

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # generate a random 16 characters in hexadecimal for secret key

# Configure the database connection
db_user = os.getenv("MYSQL_USER")
db_pass = os.getenv("MYSQL_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_pass}@db:3306/{db_name}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Define database models
class Transactions(db.Model):
    __tablename__ = "Transactions"

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    direction = db.Column(db.String(10))  # in / out / out
    truck = db.Column(db.String(50))
    containers = db.Column(db.String(10000))
    bruto = db.Column(db.Integer)
    truck_Tara_ = db.Column(db.Integer)
    neto = db.Column(db.Integer)
    produce = db.Column(db.String(50))
    sesstion_id = db.Column(db.Integer)


class Containers_registerd(db.Model):
    __tablename__ = "containers_registerd"

    container_id = db.Column(db.String(15), primary_key=True)
    weight = db.Column(db.Integer)
    unit = db.Column(db.String(10))


# helpter functions for db queries


# convert string to datetime
def str_to_datetime(ts):
    return datetime.strptime(ts, "%Y%m%d%H%M%S")


def get_query_transactions(from_date, to_date, direction_filter, item_filter):
    query = Transactions.query
    if from_date:
        query = query.filter(Transactions.datetime >= from_date)
    if to_date:
        query = query.filter(Transactions.datetime <= to_date)
    if direction_filter in ["in", "out"]:
        query = query.filter(Transactions.direction == direction_filter)
    if item_filter:
        query = query.filter(Transactions.produce == item_filter)
    return query.all()


# endpoint definitions


@app.route("/health", methods=["GET"])
def health():
    return Response("Service is running", status=200)


@app.route("/weight", methods=["GET"])
def get_weight():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    filter_value = request.args.get("filter")
    relevent_transactions = get_query_transactions(from_date, to_date, filter_value, None)
    results = []
    for transaction in relevent_transactions:
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
    direction = request.form["direction"]
    truck = request.form["licence"]
    weight = request.form["weight"]
    containers = request.form["containers"]
    unit = request.form["unit"]
    force = request.form["force"]
    produce = request.form["produce"]
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    handle_session(direction, truck)  # handle the sessions

    # todo add everything into db


@app.route("/item/<item_id>", methods=["GET"])
def get_item(item_id):
    raw_from = request.args.get("from")
    raw_to = request.args.get("to")

    # handle date range
    if not raw_from:
        from_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        from_date = str_to_datetime(raw_from)
    if not raw_to:
        to_date = datetime.now()
    else:
        to_date = str_to_datetime(raw_to)
    # query transactions by item

    relevent_transactions = get_query_transactions(from_date, to_date, "none", item_id)
    results = []
    for transaction in relevent_transactions:
        results.append(
            {
                "id": transaction.id,
                "tara": transaction.truck_Tara_,
                "session_id": transaction.sesstion_id,
            }
        )
    if len(results) == 0:
        return ("Item not found", 404)
    return results


def handle_session(direction, truck):
    if direction == "in" or direction == "none":
        # generate session
        session["truck_id"] = truck

    elif direction == "out":
        session.pop("truck_id", None)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
