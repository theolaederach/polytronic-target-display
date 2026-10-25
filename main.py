import os
import threading

from dotenv import load_dotenv

from listener import listen
from web_server import app

# load .env file
_ = load_dotenv()

# address and port for the tcp listener
listen_ip = os.getenv("URL_LISTENER", "0.0.0.0")
listen_port = int(os.getenv("PORT_LISTENER", "4000"))

if __name__ == "__main__":
    listener_thread = threading.Thread(
        target=listen,
        kwargs={"host": listen_ip, "port": listen_port},
        daemon=True,
    )
    listener_thread.start()
    print(
        f"[INFO] Listener TCP démarré sur {listen_ip}:{listen_port} (thread {listener_thread.name})"
    )

    app.startWebServer()
