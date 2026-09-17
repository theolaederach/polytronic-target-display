# Title : api routes
# Author : theo.laerach
# Last update : 30.08.2026
# Description : manage api request

from flask import Blueprint, jsonify, request

from database import database_rw

api = Blueprint("api", __name__, template_folder="templates")



@api.route("/shots", methods=["GET"])
def get_shots():
    target = request.args.get("target")
    if target :
        raw_positions = database_rw.readShot(int(target)-1)
    else :
        return {"message": "ERROR, no target number", "target": target}, 400

    # Processing the tuple for js : [{ "x": -0.12, "y": 0.200, "number": 1 }, ...]
    shots = [
        {"x": x, "y": y, "number": len(raw_positions) - i}
        for i, (x, y) in enumerate(raw_positions)
    ]

    return jsonify(shots)
