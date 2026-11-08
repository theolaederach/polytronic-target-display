import os

from dotenv import load_dotenv
from flask import Blueprint, render_template

load_dotenv()
try:
    numberOfTarget = int(
        (os.getenv("NumberOfTarget", "5")),
    )
except TypeError:
    numberOfTarget = 5

routes = Blueprint("default_routes", __name__, template_folder="templates")


@routes.route("/")
def home():
    return render_template("home.html")


@routes.route("/target")
def target():
    return render_template("target.html", target_number=numberOfTarget)


@routes.route("/target/fullscreen")
def target_fs():
    return render_template("target_fs.html", target_number=5)


@routes.route("/credits")
def credits():
    return render_template("credits.html")


# @routes.route("/test")
# def test():
#    return render_template("test.html")
