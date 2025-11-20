from flask import Flask, request, session
#from datetime import datetime
from flask_sqlalchemy import  SQLAlchemy
app = Flask(__name__)
app.secret_key = "Temp"


@app.route( "/weight", methods = ["POST"])
def post_weight():
    direction = request.form["direction"]
    truck = request.form["licence"]
    weight = request.form["weight"]
    containers = request.form["containers"]
    unit = request.form["unit"]
    force = request.form["force"]
    produce = request.form["produce"]
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    handle_session(direction, truck) #handle the sessions

    #todo add everything into db


def handle_session(direction, truck):
    if direction == "in" or direction == "none":
        # generate session
        session["truck_id"] = truck

    elif direction == "out":
        session.pop("truck_id", None)

def get_containers_weight(containers):
    data = {}
    return data






if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


