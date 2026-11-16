# Title : server/extensions
# Author : Théo
# Description : Flask extensions created here and bound to the app in app.py,
#               so that blueprints can import them without circular imports.

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# CSRF protection for every POST request (token checked automatically)
csrf = CSRFProtect()

# Rate limiter, no global limit : limits are set per route
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)
