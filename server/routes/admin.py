# Title : server/routes/admin
# Author : Théo
# Description : Admin pages : login, logout and protection of the admin routes.

import logging

from flask import Blueprint, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import Response

from database.reader import get_user_by_id, get_user_by_username
from server.extensions import limiter

logger = logging.getLogger(__name__)

routes = Blueprint("admin", __name__, template_folder="templates")

# Hash checked when the username does not exist, so the response time is the
# same whether the user exists or not (prevents user enumeration by timing)
_DUMMY_HASH: str = generate_password_hash("not-a-real-password")


@routes.before_request
def require_login() -> Response | None:
    """
    Protect every route of the admin blueprint except the login page.

    Args :
        None

    Return :
        A redirect to the login page if nobody is logged in, else None
        (the request goes on and the user is available in ``g.user``).
    """
    # the login page must stay public
    if request.endpoint == f"{request.blueprint}.login":
        return None

    user_id: int | None = session.get("user_id")
    user = get_user_by_id(user_id) if user_id is not None else None

    if user is None:
        # not logged in, or the account was deleted : drop the session
        session.clear()
        return redirect(url_for(".login"))

    # make the user available in the routes and the templates
    g.user = user
    return None


@routes.route("/")
def main_page():
    return render_template("admin/base.html")


@routes.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login() -> Response | str | tuple[str, int]:
    """
    Show the login form (GET) or check the credentials (POST).

    Args :
        None

    Return :
        The login page, or a redirect to the admin home if the login succeeds.
        A failed login returns the login page with the status 401.
    """
    if request.method == "GET":
        # already logged in : no need to see the form
        if session.get("user_id") is not None:
            return redirect(url_for(".main_page"))
        return render_template("admin/login.html")

    username: str = request.form.get("username", "").strip()[:100]
    password: str = request.form.get("password", "")
    stay_logged_in: bool = request.form.get("remember") == "on"

    user = get_user_by_username(username)

    # always compute a hash check, with a dummy hash if the user is unknown
    hash_to_check: str = user.password_hash if user else _DUMMY_HASH
    password_ok: bool = check_password_hash(hash_to_check, password)

    if user is None or not password_ok:
        logger.warning(
            "Failed admin login (username=%r, ip=%s)", username, request.remote_addr
        )
        # same message whether the username or the password is wrong
        return render_template("admin/login.html", error="Invalid credentials"), 401

    # new session : avoids reusing a session id that existed before the login
    session.clear()
    session["user_id"] = user.id
    # permanent = the cookie survives the browser closing (PERMANENT_SESSION_LIFETIME)
    session.permanent = stay_logged_in
    logger.info("Admin login (username=%r, ip=%s)", username, request.remote_addr)
    return redirect(url_for(".main_page"))


@routes.route("/logout")
def logout() -> Response:
    """
    Log the user out by emptying the session.

    Args :
        None

    Return :
        A redirect to the login page.
    """
    session.clear()
    return redirect(url_for(".login"))
