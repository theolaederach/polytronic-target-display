# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : file who init the project and the web server. Run this file to start the project.


from flask import Flask

from server.api.shots import api
from server.routes.app_routes import routes

app = Flask(__name__)

app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(routes, url_prefix="/")


def startWebServer():

    app.run(debug=True, use_reloader=False)
