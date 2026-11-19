# Title : server/routes/admin
# Author : Théo
# Description : Admin pages : login, logout and protection of the admin routes.

import logging
from typing import NamedTuple

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.datastructures import MultiDict
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import Response

from database.reader import (
    Society,
    count_group_programms,
    get_group,
    get_user_by_id,
    get_user_by_username,
    group_exists,
    list_groups,
    list_societies,
)
from database.writer import create_group, delete_group, update_group
from server.extensions import limiter

logger = logging.getLogger(__name__)

# Limits of the group form (the shooter number is an INT in the database)
MAX_GROUP_NAME_LENGTH: int = 100
MAX_SHOOTERS_PER_GROUP: int = 4
MAX_SHOOTER_NUMBER: int = 2_147_483_647

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


@routes.route("/societies")
def societies_page():
    return render_template("admin/societies.html")


class GroupForm(NamedTuple):
    """The checked content of the group form."""

    name: str
    society_id: int | None
    shooter_numbers: list[int]
    errors: list[str]


def parse_group_form(form: MultiDict, society_ids: set[int]) -> GroupForm:
    """
    Read and check the fields of the group form.

    Args :
        form (MultiDict): the submitted form (request.form).
        society_ids (set[int]): ids of the societies that exist in the database.

    Return :
        The checked values (GroupForm). If ``errors`` is not empty, the form
        must not be saved. The shooter numbers are packed without the empty
        fields, in the order of the form.
    """
    errors: list[str] = []

    # --- name
    name: str = form.get("name", "").strip()
    if not name:
        errors.append("The group name is required.")
    elif len(name) > MAX_GROUP_NAME_LENGTH:
        errors.append(f"The group name is too long (max {MAX_GROUP_NAME_LENGTH}).")

    # --- society : the id must be one of the societies of the database
    society_id: int | None = None
    raw_society: str = form.get("society", "").strip()
    if (
        raw_society.isascii()
        and raw_society.isdigit()
        and int(raw_society) in society_ids
    ):
        society_id = int(raw_society)
    else:
        errors.append("Please select a society from the list.")

    # --- shooters : empty fields are allowed, the others must be valid numbers
    shooter_numbers: list[int] = []
    shooter_errors: list[str] = []
    for position in range(1, MAX_SHOOTERS_PER_GROUP + 1):
        raw_number: str = form.get(f"shooter_{position}", "").strip()
        if not raw_number:
            continue

        if not (raw_number.isascii() and raw_number.isdigit()):
            shooter_errors.append(
                f"Shooter {position}: the number must be a whole number."
            )
        elif not 1 <= int(raw_number) <= MAX_SHOOTER_NUMBER:
            shooter_errors.append(f"Shooter {position}: the number is out of range.")
        else:
            shooter_numbers.append(int(raw_number))

    if not shooter_numbers and not shooter_errors:
        shooter_errors.append("Add at least one shooter.")

    if len(set(shooter_numbers)) != len(shooter_numbers):
        shooter_errors.append("A shooter can only be in a group once.")

    errors += shooter_errors

    return GroupForm(name, society_id, shooter_numbers, errors)


@routes.route("/groups", methods=["GET", "POST"])
def groups_page() -> Response | str | tuple[str, int]:
    """
    Show the groups page (GET) or create a group from the form (POST).

    Args :
        None

    Return :
        The page with the form and the list of groups. After a valid POST,
        a redirect to the page (so a refresh does not send the form again).
        An invalid form returns the page with the errors (status 400).
    """
    societies = list_societies()
    errors: list[str] = []
    status: int = 200

    if request.method == "POST":
        form = parse_group_form(request.form, {society.id for society in societies})
        errors = form.errors

        # the name must be free in this society (checked only on valid fields)
        if not form.society_id:
            errors.append("No society id.")
            status = 500

        elif not errors and group_exists(form.name, form.society_id):
            errors.append("This society already has a group with this name.")

        if errors or not form.society_id:
            status = 400
        elif create_group(form.name, form.society_id, form.shooter_numbers) is None:
            errors.append("The group could not be saved, see the server logs.")
            status = 500
        else:
            logger.info("Group created (name=%r, user=%s)", form.name, g.user.username)
            flash(f"Group “{form.name}” created.", "success")
            # 303 : the browser reloads the page with a GET
            return redirect(url_for(".groups_page"), code=303)

    # on error, the form is filled again with what the user typed
    values = request.form if request.method == "POST" else None
    return _render_groups_page(societies, errors, values, status=status)


def _render_groups_page(
    societies: list[Society],
    errors: list[str] | None = None,
    values: MultiDict | None = None,
    edit_errors: list[str] | None = None,
    edit_values: MultiDict | None = None,
    edit_group_id: int | None = None,
    status: int = 200,
) -> tuple[str, int]:
    """
    Render the groups page with the form, the list and the edit popup.

    Args :
        societies (list[Society]): the societies of the select fields.
        errors (list[str] | None): errors of the creation form.
        values (MultiDict | None): what the user typed in the creation form.
        edit_errors (list[str] | None): errors of the edit popup.
        edit_values (MultiDict | None): what the user typed in the edit popup.
        edit_group_id (int | None): group of the edit popup. If set, the popup
            is opened when the page loads (to show the errors).
        status (int): HTTP status of the response.

    Return :
        The page and its status (tuple).
    """
    page = render_template(
        "admin/groups.html",
        societies=societies,
        groups=list_groups(),
        errors=errors or [],
        values=values or {},
        edit_errors=edit_errors or [],
        edit_values=edit_values or {},
        edit_group_id=edit_group_id,
        max_shooters=MAX_SHOOTERS_PER_GROUP,
    )
    return page, status


@routes.route("/groups/<int:group_id>/edit", methods=["POST"])
def edit_group(group_id: int) -> Response | tuple[str, int]:
    """
    Change the name, the society and the shooters of a group (edit popup).

    Args :
        group_id (int): id of the group, from the URL.

    Return :
        A redirect to the groups page if the group is saved. An invalid form
        returns the page with the popup open and the errors (status 400).
    """
    if get_group(group_id) is None:
        flash("This group does not exist anymore.", "error")
        return redirect(url_for(".groups_page"), code=303)

    societies = list_societies()
    form = parse_group_form(request.form, {society.id for society in societies})
    errors = form.errors

    # the name must be free in this society, the group itself is ignored
    if not form.society_id:
        errors.append("No society id.")
        status = 500

    elif not errors and group_exists(form.name, form.society_id, exclude_id=group_id):
        errors.append("This society already has a group with this name.")

    status: int = 400
    if not errors and form.society_id:
        if update_group(group_id, form.name, form.society_id, form.shooter_numbers):
            logger.info(
                "Group updated (id=%d, name=%r, user=%s)",
                group_id,
                form.name,
                g.user.username,
            )
            flash(f"Group “{form.name}” updated.", "success")
            return redirect(url_for(".groups_page"), code=303)

        errors.append("The group could not be saved, see the server logs.")
        status = 500

    return _render_groups_page(
        societies,
        edit_errors=errors,
        edit_values=request.form,
        edit_group_id=group_id,
        status=status,
    )


@routes.route("/groups/<int:group_id>/delete", methods=["POST"])
def remove_group(group_id: int) -> Response:
    """
    Delete a group. A group used by programms is kept, to not lose their results.

    Args :
        group_id (int): id of the group, from the URL.

    Return :
        A redirect to the groups page, with a message.
    """
    group = get_group(group_id)
    if group is None:
        flash("This group does not exist anymore.", "error")
        return redirect(url_for(".groups_page"), code=303)

    programm_count = count_group_programms(group_id)
    if programm_count:
        flash(
            f"Group “{group.name}” cannot be deleted: "
            f"it is used by {programm_count} programm(s).",
            "error",
        )
    elif delete_group(group_id):
        logger.info(
            "Group deleted (id=%d, name=%r, user=%s)",
            group_id,
            group.name,
            g.user.username,
        )
        flash(f"Group “{group.name}” deleted.", "success")
    else:
        flash("The group could not be deleted, see the server logs.", "error")

    return redirect(url_for(".groups_page"), code=303)


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
