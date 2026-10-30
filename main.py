# main.py
import argparse
import os
import sys
import threading

from dotenv import load_dotenv

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
        type=int,
        default=int(os.getenv("PORT_WEB_SERVER", "5000")),
        help="Setup the port of the web server, DEFAULT 5000",
    )

    # Listener settings
    parser.add_argument(
        "--listener_only",
        action="store_true",
        help="Start the TCP listener without the web server",
    )
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
    #check if the .env file exist
    if not os.path.exists(".env"):
        print(".env file not found. Exiting.")
        sys.exit(1)

    args = get_args()
    if args.web_server_only and args.listener_only:
        raise argparse.ArgumentError(
            None,
            "You must choose whether you want to run only the web server or only the TCP listener !!!",
        )

    if args.listener_only:
        from listener import listen

        listen(host=args.listen_ip, port=args.listen_port)

    elif not args.web_server_only:
        from listener import listen

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

    if not args.listener_only:
        from server import app

        app.startWebServer(
            host=args.web_server_host,
            port=args.web_server_port,
        )
