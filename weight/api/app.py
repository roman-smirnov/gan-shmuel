from datetime import datetime, timezone
from flask import Flask, Response, request, session
from flask_sqlalchemy import SQLAlchemy
import secrets
import os

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.secret_key = secrets.token_hex(6)  # generate a random 12 characters in hexadecimal for secret key

# Configure the database connection
db_user = os.getenv("MYSQL_USER")
db_pass = os.getenv("MYSQL_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_pass}@db:3306/{db_name}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def convert_kg_to_lbs(kg_num):
    return int(float(kg_num)*2.20)

def convert_lbs_to_kg(lbs_num):
    return int(float(lbs_num) / 2.20)

def calc_containers_weight(containers):
    #todo: take into consideration weight unit differences
    #the function receives a list(string separated by ",") of containers
    #the function return the total weight of the containers or na if there was an issue
    total_weight = 0
    try:
        id_list = [int(i) for i in containers.split(",")]  # creates a list of id from the containers
        results = (db.session.query(Containers_registered.weight, Containers_registered.unit).filter
                   (Containers_registered.container_id.in_(id_list)).all())  # get list of tuples with all container weight
        if len(results) < len(id_list):
            return None
        for value in results:  # loops on all list
            if value[1] == "kg":
                total_weight = total_weight + value[0]
            else:
                total_weight = total_weight + convert_lbs_to_kg(value[0])
        return total_weight

    except: #except will raise in case the container wasn't found  and return na
        return None


def calc_neto_fruit(bruto_weight,truck_tara, containers):
    #this functions receives a bruto weight, truck tara and a list(string separated by ",") of containers
    #and returns the neto weight by the following calculation neto = brutu - truck tara - containers_tara
    container_weight = calc_containers_weight(containers)
    if container_weight:
        return bruto_weight - (int(truck_tara) + container_weight)

    else:
        return None


    print("issue with calculating ")
    return None
    #pass containers to containers db

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


# helpter functions for db queries


# convert string to datetime
def str_to_datetime(ts):
    return datetime.strptime(ts, "%Y%m%d%H%M%S")

def get_query_transactions(from_date=None, to_date=None, direction_filter=None, item_filter=None, truck_filter=None):
    try:
        query = Transactions.query
        if from_date:
            query = query.filter(Transactions.datetime >= from_date)
        if to_date:
            query = query.filter(Transactions.datetime <= to_date)
        if direction_filter in ["in", "out"]:
            query = query.filter(Transactions.direction == direction_filter)
        if item_filter:
            query = query.filter(Transactions.produce == item_filter)
        if truck_filter:
            query = query.filter(Transactions.truck == truck_filter)
        return query.all()
    except IndexError:
        return None


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

def update_row(old_row, new_row):
    old_row.neto = new_row.neto
    old_row.bruto = new_row.bruto
    old_row.containers = new_row.containers
    old_row.truck = new_row.truck
    old_row.produce = new_row.produce
    db.session.commit()

    return 1

def verbose(row):
    #the function receives a transaction row
    #the functions return json for post weight return value
    if row.direction == "out":
        return {
            "id": row.id,
            "truck": row.truck,
            "bruto": row.bruto,
            "truckTara": row.truckTara,
            "neto": row.neto
        }
    else:
        return {
            "id": row.id,
            "truck": row.truck,
            "bruto": row.bruto
        }

@app.route("/weight", methods=["POST"])
def post_weight():

    data = request.form.to_dict()
    #last_row = Transactions.query.order_by(Transactions.id.desc()).first()
    last_row = None
    rows = get_query_transactions(truck_filter=data["truck"]) #get the last transaction of the truck
    if rows:
        last_row = rows[-1]

    new_row = Transactions()
    new_row.produce = data["produce"]
    new_row.bruto = int(data["weight"])
    new_row.direction = data["direction"]
    new_row.neto = None
    new_row.truck = int(data["truck"])
    new_row.containers = data["containers"]
    new_row.truckTara = None
    handle_session(new_row, data["direction"], data["truck"])  # handle the sessions
    if last_row: #check if the last row exist

        if last_row.direction == "in" and new_row.direction == "out":
            containers_weight = calc_containers_weight(new_row.containers)
            if containers_weight:
                new_row.truckTara = new_row.bruto - calc_containers_weight(new_row.containers)
                neto = calc_neto_fruit(int(last_row.bruto), new_row.truckTara, data["containers"])
                new_row.neto = neto

        if (( last_row.direction == "in" and last_row.direction == new_row.direction )
            or (last_row.direction == "out" and last_row.direction == new_row.direction)):

            if not data["force"]:
                raise Exception(f"truck already {last_row.direction} use force True to update")
            elif data["force"] == "True":
                update_row(last_row,new_row )
                return verbose(last_row)
            else:
                raise Exception(f"truck already {last_row.direction} use force True to update")

    db.session.add(new_row)
    db.session.commit()
    #
    return verbose(new_row)


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
                "session_id": transaction.session_id,
            }
        )
    if len(results) == 0:
        return ("Item not found", 404)
    return results


def handle_session(t,direction, truck):
    if direction == "in" or direction == "none":
        # generate session
        rand_num = secrets.randbelow(2000000000)#creates a random number for the
        session[truck] = rand_num
        t.session_id = rand_num

    elif direction == "out":
        rows = get_query_transactions(truck_filter=truck)  # get the last transaction of the truck
        if rows:
            last_row = rows[-1]
            session_id = last_row.session_id
            t.session_id = session_id
            session.pop(truck, None)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
