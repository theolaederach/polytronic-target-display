# Title : shots api
# Author : theo.laerach
# Last update : 30.08.2026
# Description : manage shots api request

from flask import Blueprint, jsonify, request

from database.reader import (
    getScoreSeriesOnTarget,
    getShooterNumberWithTarget,
    getTargetType,
    listLastShot,
)
from database.writer import targets

api_shots = Blueprint("api_shots", __name__, template_folder="templates")


def json_shots(target: int) -> dict:
    data_list = listLastShot(target)
    # Processing the tuple for js : [{ "x": -0.12, "y": 0.200, "number": 1, "score": 56 }, ...]
    shots = [
        {
            "x": x,
            "y": y,
            "number": len(data_list) - i,
            "score": score_base10,
        }
        # s.x, s.y, s.score_base10, s.score_base100, s.time
        for i, (x, y, score_base10, score_base100, time) in enumerate(data_list)
    ]

    reponse = {
        "shooter_number": getShooterNumberWithTarget(target),
        "target_type": getTargetType(target),
        "total_score": getScoreSeriesOnTarget(target),
        "shots": shots,
    }

    return reponse


@api_shots.route("/targets", methods=["GET"])
def get_shots():
    raw_target = request.args.get("target")

    if raw_target and raw_target.isdigit() and int(raw_target) > 0:
        target = int(raw_target) - 1
    else:
        return jsonify(
            {"message": "ERROR, invalid target number", "target": raw_target}
        ), 400

    return jsonify(json_shots(target))


@api_shots.route("/targets/all", methods=["GET"])
def get_all_targets():
    list_of_last_shots: list[dict] = []

    for t in targets:
        list_of_last_shots.append(json_shots(t.target_number))

    reponse = {"targets": list_of_last_shots}
    return jsonify(reponse)
