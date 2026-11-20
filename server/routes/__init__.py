from flask import Blueprint

from server.routes import admin, default_routes, statistics

routes = Blueprint("routes", __name__, template_folder="templates")

routes.register_blueprint(default_routes.routes, url_prefix="/")
routes.register_blueprint(statistics.routes, url_prefix="/statistics")
routes.register_blueprint(admin.routes, url_prefix="/admin")
