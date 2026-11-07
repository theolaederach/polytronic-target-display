import os

from dotenv import load_dotenv
from flask import Blueprint, render_template

import database.reader as r

load_dotenv()
try:
    numberOfTarget = int(
        (os.getenv("NumberOfTarget", "5")),
    )
except TypeError:
    numberOfTarget = 5

routes = Blueprint("routes", __name__, template_folder="templates")


@routes.route("/")
def home():
    return render_template("home.html")


@routes.route("/target")
def target():
    return render_template("target.html", target_number=numberOfTarget)


@routes.route("/target/fullscreen")
def target_fs():
    return render_template("target_fs.html", target_number=5)


@routes.route("/statistics")
@routes.route("/statistics/<int:shooter_id>")
def statistics(shooter_id=None):
    if shooter_id:
        shooter_info = r.getShooterWithId(shooter_id)
        if shooter_info is not None:
            shooter_number, name = shooter_info
        else:
            shooter_number, name = (None, "")
        data_shots = {
            "shots": r.getAllShots(int(shooter_id)),
            "shooter_number": shooter_number,
            "shooter_name": name,
        }
    else:
        data_shots = None
    return render_template("statistics.html", data=data_shots)


@routes.route("/credits")
def credits():
    return render_template("credits.html")


# @routes.route("/test")
# def test():
#    return render_template("test.html")
