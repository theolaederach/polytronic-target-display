from flask import Blueprint, render_template

import database.reader as r

routes = Blueprint("statistics", __name__, template_folder="templates")


@routes.route("/")
@routes.route("/<int:shooter_id>")
def getStatistics(shooter_id=None):
    if shooter_id:
        shooter_info = r.getShooterWithId(shooter_id)
        if shooter_info is not None:
            shooter_number, name = shooter_info
        else:
            shooter_number, name = (None, "")
        data_shots = {
            "shooter_number": shooter_number,
            "shooter_name": name,
            "shots": r.getAllShots(int(shooter_id)),
            "programm": r.getAllProgramm(int(shooter_id)),
        }
    else:
        data_shots = None
    return render_template("statistics.html", data=data_shots)


@routes.route("/programm/")
@routes.route("/programm/<int:programm_id>")
def getProgramm(programm_id=None):
    if programm_id:
        series = []
        for id in r.getAllSeriesIdByProgrammId(programm_id):
            series.append(r.getShotsBySeriesId(id))

        data = {"programm": r.getProgrammById(programm_id), "series": series}
    else:
        data = None
    return render_template("programm.html", data=data)
