# main.py
import argparse
import os
import threading

from dotenv import load_dotenv

from listener import listen
from web_server import app

load_dotenv()


def get_args():
    parser = argparse.ArgumentParser(description="Polytronic Target‑Display launcher")
    parser.add_argument(
        "--web_server_only",
        action="store_true",
        help="Démarrer uniquement le serveur web (sans écoute TCP)",
    )
    # Vous pouvez ajouter d’autres options, par ex. l’IP/port d’écoute
    parser.add_argument(
        "--listen-ip",
        default=os.getenv("URL_LISTENER", "0.0.0.0"),
        help="Adresse d’écoute TCP (défaut: 0.0.0.0)",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=int(os.getenv("PORT_LISTENER", "4000")),
        help="Port d’écoute TCP (défaut: 4000)",
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
    app.startWebServer()
