from flask import Blueprint, render_template

routes = Blueprint("admin", __name__, template_folder="templates")


@routes.route("/")
def main_page():
    return render_template("admin/base.html")
