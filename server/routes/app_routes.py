from flask import Blueprint, render_template

import database.reader as r

routes = Blueprint("routes", __name__, template_folder="templates")


@routes.route("/")
def home():
    return render_template("home.html")


@routes.route("/target")
def target():
    return render_template("target.html")


@routes.route("/target/fullscreen")
def target_fs():
    return render_template("target_fs.html")


@routes.route("/statistics")
@routes.route("/statistics/<int:shooter_id>")
def statistics(shooter_id=None):
    if shooter_id:
        data = {"shots": r.getAllShots(int(shooter_id))}
    else:
        data = None
    print("data", shooter_id, data)
    return render_template("statistics.html", data=data)


@routes.route("/credits")
def credits():
    return render_template("credits.html")


# @routes.route("/test")
# def test():
#    return render_template("test.html")
