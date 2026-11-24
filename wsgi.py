# Title : wsgi
# Author : Théo
# Description : Entry point used by gunicorn (see the Dockerfile).
#               It does what main.py does when the project starts: it launches
#               the TCP listener and the weather updater in background threads,
#               then exposes the Flask app.
#
#               WARNING : gunicorn must run with ONE worker only. The listener
#               writes in the `targets` list (in memory) and the API reads it,
#               so both must live in the same process.

import logging
import threading

from dotenv import load_dotenv

load_dotenv()

# Same format as main.py, `force` replaces the handlers already installed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s : %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

from listener import listen  #  (needs the .env to be loaded first)
from server.app import app

_ = app
from server.weather import startWeatherUpdater


def _run_listener() -> None:
    """
    Run the TCP listener and log the error if it stops.

    Args :
        None

    Return :
        None
    """
    try:
        # host and port come from HOST_LISTENER and PORT_LISTENER
        listen()
    except Exception:
        # without this, the thread would die and the web server would keep
        # running without receiving any shot
        logger.exception("The TCP listener stopped")


def start_background_services() -> None:
    """
    Start the TCP listener and the weather updater.

    Args :
        None

    Return :
        None
    """
    # daemon thread: it stops with the process
    listener_thread = threading.Thread(
        target=_run_listener, name="tcp-listener", daemon=True
    )
    listener_thread.start()
    logger.info("TCP listener thread started (%s)", listener_thread.name)

    startWeatherUpdater()


# executed once, when gunicorn imports this module in its worker
start_background_services()
