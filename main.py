# main.py
import argparse
import os
import threading

from dotenv import load_dotenv

from listener import listen
from server import app

load_dotenv()


def get_args():
    parser = argparse.ArgumentParser(description="Polytronic Target‑Display launcher")

    # Web server settings
    parser.add_argument(
        "--web_server_only",
        action="store_true",
        help="Start the web server without the tcp listening",
    )
    parser.add_argument(
        "--web_server-host",
        default=os.getenv("HOST_WEB_SERVER", "0.0.0.0"),
        help="Setup the host of the web server, DEFAULT 0.0.0.0",
    )
    parser.add_argument(
        "--web_server-port",
        default=int(os.getenv("PORT_WEB_SERVER", "5000")),
        help="Setup the port of the web server, DEFAULT 5000",
    )

    # Listener settings
    parser.add_argument(
        "--listen-ip",
        default=os.getenv("URL_LISTENER", "0.0.0.0"),
        help="Listen address TCP (défaut: 0.0.0.0)",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=int(os.getenv("PORT_LISTENER", "4000")),
        help="Listen port TCP (défaut: 4000)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    # Si l’option `--web_server_only` est **absente**,
    # on lance le thread d’écoute TCP.
    if not args.web_server_only:
        listener_thread = threading.Thread(
            target=listen,
            kwargs={"host": args.listen_ip, "port": args.listen_port},
            daemon=True,
        )
        listener_thread.start()
        print(
            f"[INFO] Listener TCP démarré sur {args.listen_ip}:{args.listen_port} "
            f"(thread {listener_thread.name})"
        )

    # Start the web server
    app.startWebServer(host=args.web_server_host,
        port=args.web_server_port
    )
