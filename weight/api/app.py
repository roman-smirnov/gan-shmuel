from datetime import datetime, timezone
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return Response('Service is running', status=200)

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://root@localhost:3306/gan_shmuel"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Weighing(db.Model):
    __tablename__ = "weighings"

    id = db.Column(db.String(50), primary_key=True)  
    direction = db.Column(db.String(10))  
    truck = db.Column(db.String(20))  
    bruto_kg = db.Column(db.Integer)
    neto_kg = db.Column(db.Integer)
    produce = db.Column(db.String(50))  
    containers = db.Column(db.Text)  
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


@app.route("/weight", methods=["GET"])
def get_weight():
    return "Weight data"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)
