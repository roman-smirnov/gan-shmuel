import secrets
from datetime import datetime
from flask import session, abort, request


# dependencies to be injected from app.py
db = None
Transactions = None
Containers_registered = None


# ---
# calculate helper functions
# ---
def calc_containers_weight(containers):
    # todo: take into consideration weight unit differences
    # the function receives a list(string separated by ",") of containers
    # the function return the total weight of the containers or na if there was an issue

    total_weight = 0

    if not containers:  # check if there are no containers
        return total_weight
    try:
        id_list = containers.split(",")  # creates a list of id from the containers
        results = (
            db.session.query(Containers_registered.weight, Containers_registered.unit)
            .filter(Containers_registered.container_id.in_(id_list))
            .all()
        )  # get list of tuples with all container weight
        if len(results) < len(
            id_list
        ):  # check if less containers returned than the amount sent
            return None
        for (
            value
        ) in results:  # loops on all list and convert the size into kg if needed
            total_weight = total_weight + convert_to_kg(value[0], value[1])
            # value[0] = container weight , value[1] = container unit
        return total_weight

    except (
        Exception
    ):  # except will raise in case the container wasn't found  and return na
        return None


def calc_neto_fruit(bruto_weight, truckTara, containers):
    # this functions receives a bruto weight, truck tara and a list(string separated by ",") of containers
    # and returns the neto weight by the following calculation neto = brutu - truck tara - containers_tara
    container_weight = calc_containers_weight(containers)
    if container_weight or len(containers) == 0:
        return bruto_weight - (int(truckTara) + container_weight)

    else:
        return None


def convert_kg_to_lbs(kg_num):
    return int(round(float(kg_num) * 2.20))


def convert_metric_ton_to_kg(ton_num):
    return int(ton_num * 1000)


def convert_usa_ton_to_kg(ton_num):
    return int(round(float(ton_num) * 907.2))


def convert_lbs_to_kg(lbs_num):
    return int(round(float(lbs_num) / 2.20))


def convert_uk_long_ton_to_kg(uk_l_weight):
    return int(uk_l_weight * 1016)


def convert_to_kg(weight, unit=""):
    # function receives a weight and unit size and convert it to kg
    # if the unit type isn't supported it will return None
    unit_lower = unit.lower()
    metric_ton = ["t", "tonne", "metric ton", "metric_ton", "mt"]
    us_ton = ["st", "short ton", "short_ton", "us ton", "us_ton", "ust"]
    kilogram = ["kg", "kilogram"]
    pound = ["lb", "lbs", "pound", "pounds", "lbm"]
    uk_l_ton = ["lt", "long ton", "long_ton", "imperial ton", "imperial_ton"]
    if unit and weight:
        if unit_lower in kilogram:
            return weight
        elif unit_lower in pound:
            return convert_lbs_to_kg(weight)
        elif unit_lower in us_ton:
            return convert_usa_ton_to_kg(weight)
        elif unit_lower in metric_ton:
            return convert_metric_ton_to_kg(weight)
        elif unit_lower in uk_l_ton:
            return convert_uk_long_ton_to_kg(weight)

        elif unit == "":
            return None

    return None


# ---
# query helper functions
# ---


# convert string to datetime
def str_to_datetime(ts):
    return datetime.strptime(ts, "%Y%m%d%H%M%S")


def get_query_transactions(
    from_date=None,
    to_date=None,
    direction_filter=None,
    container_filter=None,
    truck_filter=None,
):
    query = Transactions.query
    if from_date:
        query = query.filter(Transactions.datetime >= from_date)
    if to_date:
        query = query.filter(Transactions.datetime <= to_date)
    if direction_filter in ["in", "out"]:
        query = query.filter(Transactions.direction == direction_filter)
    if container_filter:
        query = query.filter(Transactions.containers == container_filter)
    if truck_filter:
        query = query.filter(Transactions.truck == truck_filter)
    return query.all()


# ---
# other helper functions
# ---
def update_row(old_row, new_row):
    old_row.neto = new_row.neto
    old_row.bruto = new_row.bruto
    old_row.containers = new_row.containers
    old_row.truck = new_row.truck
    old_row.produce = new_row.produce
    db.session.commit()

    return 1


def verbose(row):
    # the function receives a transaction row
    # the functions return json for post weight return value
    if row.direction == "out":
        return {
            "id": row.id,
            "truck": row.truck,
            "bruto": row.bruto,
            "truckTara": row.truckTara,
            "neto": row.neto,
        }
    else:
        return {"id": row.id, "truck": row.truck, "bruto": row.bruto}


def handle_session(new_row, direction, truck):
    if direction == "in" or direction == "none":
        # generate session
        rand_num = secrets.randbelow(2000000000)  # creates a random number for the
        session[truck] = rand_num
        new_row.session_id = rand_num

    elif direction == "out":
        rows = get_query_transactions(
            None, None, None, None, truck
        )  # get the last transaction of the truck
        if rows:
            last_row = rows[-1]
            session_id = last_row.session_id
            new_row.session_id = session_id
            session.pop(truck, None)


def is_ui_mode():
    return request.args.get("ui") == "1" or request.form.get("ui") == "1"
