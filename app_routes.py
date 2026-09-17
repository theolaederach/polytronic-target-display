from flask import Blueprint, render_template

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

@routes.route("/credits")
def credits():
    return render_template("credits.html")


@routes.route("/test")
def test():
    return render_template("test.html")
