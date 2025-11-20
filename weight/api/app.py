from datetime import datetime, timezone
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)


# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://root@localhost:3306/gan_shmuel"
)
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


# endpoint definitions


@app.route("/health", methods=["GET"])
def health():
    return Response("Service is running", status=200)


@app.route("/weight", methods=["GET"])
def get_weight():
    return "Weight data"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
