# Title : shooters api
# Author : theo.laerach
# Last update : 03.11.2026
# Description : return the list of the user

from flask import Blueprint, jsonify

import database.reader as r

api_shooters = Blueprint("api_shooters", __name__, template_folder="templates")


@api_shooters.route("/name/all")
def allShooters():
    reponse = {"shooters_number": r.getAllShooters(), "dates": r.getAllDates()}
    return jsonify(reponse)
