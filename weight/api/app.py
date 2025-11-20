import flask 

app = flask.Flask(__name__)

@app.route("/heaith", methods=["GET"])
def heaith();
    return "OK"
    




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


