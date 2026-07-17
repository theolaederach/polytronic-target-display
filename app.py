# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : file who init the project and the web server. Run this file to start the project.

from flask import Flask

from app_api import api
from app_routes import routes

app = Flask(__name__)

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(routes,url_prefix='/')



if __name__ == '__main__':
    app.run(debug=True)
