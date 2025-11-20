import flask 
from flask import Response


app = flask.Flask(__name__)

@app.route("/health", methods=["GET"])
def health();
    return Response('Okay', 200)





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


