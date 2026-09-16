# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : file who init the project and the web server. Run this file to start the project.

import os
import threading

from dotenv import load_dotenv
from flask import Flask

from app_api import api
from app_routes import routes
from database.receiver import listen

app = Flask(__name__)

app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(routes, url_prefix="/")

# load .env file
_ = load_dotenv()

# address and port for the tcp listener
listen_ip = os.getenv("URL_LISTENER", "0.0.0.0")
listen_port = int(os.getenv("PORT_LISTENER", "4000"))

if __name__ == "__main__":
    receiver_thread = threading.Thread(
        target=listen,
        kwargs={"host": listen_ip, "port": listen_port},
        daemon=True,
    )
    receiver_thread.start()
    print(
        f"[INFO] Listener TCP démarré sur {listen_ip}:{listen_port} (thread {receiver_thread.name})"
    )

    app.run(debug=True)
