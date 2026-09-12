# Title : api routes
# Author : theo.laerach
# Last update : 30.08.2026
# Description : manage api request

from flask import Blueprint, jsonify

from database import database

api = Blueprint("api", __name__, template_folder="templates")


@api.route("/")
def hello_world():

    return "Hello, World! This is the url from the api"


@api.route("/shots", methods=["GET"])
def get_shots():
    # The shots are stocked in tuple in list [(x,y),(x,y)]
    raw_positions = database.readShot(1779)

    # Processing the tuple for js : [{ "x": -0.12, "y": 0.200, "number": 1 }, ...]
    shots = [
        {"x": x, "y": y, "number": len(raw_positions) - i}
        for i, (x, y) in enumerate(raw_positions)
    ]

    return jsonify(shots)
