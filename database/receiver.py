"""
Database socket receiver
========================

This simple script listens on TCP port 4000 on all interfaces and prints
incoming data line‑by‑line.

It is deliberately minimal – the intention is that later on a dedicated
function will replace the `print` call to process the data.

Usage
-----

```
python -m database.receiver
```

The server will keep running until it receives a keyboard interrupt.
"""

import csv
import os
import socket
import sys
from io import StringIO

from connection import targets
from write import InitTarget

port_str = os.getenv("PORT_LISTENER", "4000")
PORT = int(port_str)

HOST = os.getenv("URL_LISTENER", "0.0.0.0")

numberOfTarget_str = os.getenv("NumberOfTarget", "5")
numberOfTarget = int(numberOfTarget_str)

for target in range(numberOfTarget):
    targets.insert(target, InitTarget(target))


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
        srv.listen(1)
        print(f"Listening on {host}:{port} …")
        try:
            while True:
                conn, addr = srv.accept()
                print(f"Accepted connection from {addr[0]}:{addr[1]}")
                with conn.makefile("rb") as f:
                    for raw_line in f:
                        # Decode with fallback to latin‑1 if utf‑8 fails
                        try:
                            line = raw_line.decode("utf-8", errors="replace")
                        except UnicodeDecodeError:
                            line = raw_line.decode("latin-1", errors="replace")

                        analyse_data(line)

        except KeyboardInterrupt:
            print("\nServer stopped by user.")
            sys.exit(0)


def analyse_data(data: str = "") -> None:
    reader = csv.reader(StringIO(data), delimiter=";")
    row = next(reader)
    if row == []:
        return
    dataType = row[0]  # (_SHOT, _GRPH)
    target_number = int(row[1])  # target number base 0
    shooter_number = int(row[3])
    try:
        time = row[6]
    except IndexError:
        time = ""
        # print(row, IndexError)

    if dataType == "_DIAG":
        # Begin of a programm
        # _DIAG;3;4;1839;60;5;12:09:13.00;11;0;0;2199066336
        guid = row[10]

        targets[target_number].start_programm(shooter_number, time, guid)

    elif dataType == "_GRPH":
        # Begin of a serie
        # _GRPH;3;4;1839;60;101;12:26:52.69;8;0;0;1;0;0;1;2199172266
        series_type = int(row[9])
        guid = row[14]

        targets[target_number].start_serie(series_type, time, guid)

    elif dataType == "_SUBT":
        # Begin of a serie
        # _SUBT;3;4;1839;60;110;12:27:27.27;7;0;66;626;2199175750

        targets[target_number].serie_finish(time)

    elif dataType == "_PRST":
        # Begin of a serie
        # _SUBT;3;4;1839;60;110;12:27:27.27;7;0;66;626;2199175750

        targets[target_number].programm_finish()

    elif dataType == "_SHOT":
        # record a shot
        # _SHOT;3;4;1839;60;109;12:27:26.71;3;0;2048;8;74;0;8;0.11861770;0.06816363;900;0;0;655.35;2199175643;1;800;35
        pos_x = float(row[14])
        pos_y = float(row[15])
        score_10 = int(row[10])
        score_100 = int(row[11])
        guid = row[20]

        targets[target_number].shot(pos_x, pos_y, score_10, score_100, time, guid)
