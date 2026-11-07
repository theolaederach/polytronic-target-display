import csv
import logging
import os
import socket
import sys
import threading
from datetime import datetime
from io import StringIO

from database.writer import targets

ALLOWED_IPS = os.getenv("ALLOWED_IPS_LISTENER", "127.0.0.1").split(",")

port_str = os.getenv("PORT_LISTENER", "4000")
PORT = int(port_str)

HOST = os.getenv("HOST_LISTENER", "0.0.0.0")

logger = logging.getLogger(__name__)


def listen(host: str = HOST, port: int = PORT) -> None:
    """Start a blocking TCP server that prints each received line.

    Parameters
    ----------
    host: str
        Address to bind to.
    port: int
        Port to listen on.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        logger.debug("Listening on %s : %s …", host, port)
        try:
            while True:
                conn, addr = srv.accept()
                if addr[0] not in ALLOWED_IPS:
                    logger.warning(
                        "Rejected connection from unauthorized IP %r", addr[0]
                    )
                    conn.close()
                    continue
                t = threading.Thread(
                    target=handle_connection, args=(conn, addr), daemon=True
                )
                t.start()
        except KeyboardInterrupt:
            logger.critical("\nServer stopped by user.")
            sys.exit(0)


def handle_connection(conn, addr):
    """Process a single client connection in its own thread."""
    logger.info("[Thread] Connected %s : %s", addr[0], addr[1])
    try:
        with conn.makefile("rb") as f:
            for raw_line in f:
                line = raw_line.decode("latin-1")
                try:
                    analyse_data(line)
                except IndexError as e:
                    print(line, e)
    except Exception:
        logger.exception("Connection error %r", addr)
    finally:
        conn.close()
        logger.info("[Thread] Disconnected %s : %s", addr[0], addr[1])


def analyse_data(data: str = "") -> None:
    """Parse and dispatch the packet to the appropriate handler."""
    reader = csv.reader(StringIO(data), delimiter=";")
    row = next(reader)
    if row == []:
        return
    dataType = row[0]  # (_SHOT, _GRPH, etc.)
    if {
        "_NAME": True,
        "_PRCH": True,
        "_GRPH": True,
        "_SUBT": True,
        "_PRST": True,
        "_SHOT": True,
    }.get(dataType):
        target_number = int(row[1])  # base‑0 index
        if not (0 <= target_number < len(targets)):
            logger.error("target number invalid in the listener : %r", target_number)
            return
        shooter_number = int(row[3])
    else:
        return
    try:
        time = row[6]
    except IndexError:
        time = datetime.now().strftime("%H:%M:%S.%f")

    try:
        if dataType == "_NAME":
            name = row[5]
            targets[target_number].write_shooter(shooter_number, name)

        elif dataType == "_PRCH":
            guid = row[25]
            targets[target_number].start_programm(shooter_number, time, guid)
        elif dataType == "_GRPH":
            series_type = int(row[9])
            guid = row[14]
            targets[target_number].start_serie(series_type, time, guid)
        elif dataType == "_SUBT":
            targets[target_number].serie_finish(time)
        elif dataType == "_PRST":
            targets[target_number].programm_finish(time)
        elif dataType == "_SHOT":
            pos_x = float(row[14])
            pos_y = float(row[15])
            score_10 = int(row[10])
            score_100 = int(row[11])
            guid = row[20]
            targets[target_number].shot(pos_x, pos_y, score_10, score_100, time, guid)
    except IndentationError as e:
        logger.error(e, row)
        return
    except Exception:
        logger.exception("something wrong with the listener")
        return
