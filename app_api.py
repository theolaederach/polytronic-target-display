from flask import Blueprint, jsonify, request

from random_shot import random_shot
from write_target import write_target

api = Blueprint("api", __name__, template_folder="templates")


@api.route("/render_target", methods=["GET"])
def render_target():
    if request.method == "GET":
        target_number = request.args["target_number"]

        write_target(
            "assets/template.png", random_shot(7), f"static/target{target_number}.png"
        )
        return f"Target {target_number} written"
    else:
        return "Method not allowed"


@api.route("/")
def hello_world():
    return "Hello, World!"


@api.route("/shots", methods=["GET"])
def get_shots():
    # Si tes tirs sont stockés sous forme de liste de tuples : [(0.512, -0.220), (0.30, 0.220)]
    raw_positions = [(0.012, -0.220), (0.30, 0.220), (0.490, 0.180), (0, 0), (0.1, 0.1)]

    # Transformation des tuples pour le JS : [{ "x": -0.12, "y": 0.200, "number": 1 }, ...]
    shots = [
        {"x": x, "y": y, "number": i + 1} for i, (x, y) in enumerate(raw_positions)
    ]

    return jsonify(shots)
