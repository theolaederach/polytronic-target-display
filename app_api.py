# Title : api routes
# Author : theo.laerach
# Last update : 30.08.2026
# Description : manage api request

from flask import Blueprint, jsonify, request

from database.reader import (
    getScoreSeriesOnTarget,
    getShooterNumber,
    getTargetType,
    listLastShot,
)

api = Blueprint("api", __name__, template_folder="templates")


@api.route("/shots", methods=["GET"])
def get_shots():
    raw_target = request.args.get("target")
    if raw_target:
        target = int(raw_target) - 1
        raw_data = listLastShot(target)
    else:
        return {"message": "ERROR, no target number", "target": raw_target}, 400

    # Processing the tuple for js : [{ "x": -0.12, "y": 0.200, "number": 1, "score": 56 }, ...]
    shots = [
        {
            "x": x,
            "y": y,
            "number": len(raw_data) - i,
            "score": score,
        }
        for i, (x, y, score) in enumerate(raw_data)
    ]

    reponse = {
        "shooter_number": getShooterNumber(target),
        "target_type": getTargetType(target),
        "total_score": getScoreSeriesOnTarget(target),
        "shots": shots,
    }

    return jsonify(reponse)
