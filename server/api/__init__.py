from flask import Blueprint

from server.api import shooter, shots

api = Blueprint("api", __name__, template_folder="templates")

api.register_blueprint(shots.api_shots, url_prefix="/shots")
api.register_blueprint(shooter.api_shooters, url_prefix="/shooters")
