# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : file who init the project and the web server. Run this file to start the project.


import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from server.api import api
from server.extensions import csrf, limiter
from server.routes import routes
from server.weather import startWeatherUpdater

load_dotenv()
logger = logging.getLogger(__name__)

app = Flask(__name__)

# The secret key signs the session cookie : without it, no login is possible
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    logger.fatal("SECRET_KEY is missing in the .env file")
    raise RuntimeError("SECRET_KEY is missing in the .env file")

app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,  # cookie not readable from JavaScript
    SESSION_COOKIE_SAMESITE="Lax",  # cookie not sent on cross-site POST
    # only send the cookie over HTTPS (set to true in production)
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    # lifetime of the cookie when "stay logged in" is checked
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

# Bind the extensions to the app
csrf.init_app(app)
limiter.init_app(app)

app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(routes, url_prefix="/")


def startWebServer(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    startWeatherUpdater()
    app.run(host=host, port=port, debug=debug, use_reloader=False)
