# Title : database/reader
# Author : Théo
# Last update : 27.10.2026
# Description : Module for read the database with function like listScore()

import logging
from datetime import datetime, time
from typing import NamedTuple

import mariadb

from database.connection import execute_request


def get_current(target_number: int) -> tuple[int | None, int | None]:
    """Return (programm_id, series_id) of the target, read from the db."""
    rows = execute_request(
        "SELECT programm_id, series_id FROM current WHERE target_number = ?",
        (target_number,),
    )
    return (rows[0][0], rows[0][1]) if rows else (None, None)


logger = logging.getLogger(__name__)


class User(NamedTuple):
    """A row of the users table."""

    id: int
    username: str
    password_hash: str
    role: str


def _fetch_user(request: str, params: tuple) -> User | None:
    """
    Run a SELECT on the users table and build a User from the first row.

    Args :
        request (str): SQL statement selecting id, username, password_hash, role.
        params (tuple): values that replace the "?" placeholders.

    Return :
        The user (User), or None if no row matches.
    """
    try:
        rows = execute_request(request, params)
    except mariadb.Error:
        logger.exception("DB reading error on the users table")
        raise

    if not rows:
        return None

    # init the user from the first row
    return User(*rows[0])


def get_user_by_username(username: str) -> User | None:
    """
    Get a user from his username.

    Args :
        username (str): the login name.

    Return :
        The user (User), or None if the username does not exist.
    """
    request = "SELECT id, username, password_hash, role FROM users WHERE username = ?"
    return _fetch_user(request, (username,))


def get_user_by_id(user_id: int) -> User | None:
    """
    Get a user from his id.

    Args :
        user_id (int): the id of the user.

    Return :
        The user (User), or None if the id does not exist.
    """
    request = "SELECT id, username, password_hash, role FROM users WHERE id = ?"
    return _fetch_user(request, (user_id,))


def _society_label(society_id: int, name: str | None, location: str | None) -> str:
    """
    Build the text shown for a society, for example "Tir Club (Lausanne)".

    Args :
        society_id (int): id of the society, used if it has no name and no location.
        name (str | None): name of the society.
        location (str | None): location of the society.

    Return :
        The label of the society (str).
    """
    parts = [name or "", f"({location})" if location else ""]
    return " ".join(part for part in parts if part) or f"Society {society_id}"


class Society(NamedTuple):
    """A row of the societies table, with the text to show in the pages."""

    id: int
    label: str


class GroupShooter(NamedTuple):
    """A shooter of a group. The name is None until the listener receives it."""

    number: int
    name: str | None


class Group(NamedTuple):
    """A group with its society and its shooters (4 slots, None if empty)."""

    id: int
    name: str
    society_id: int | None
    society: str
    shooters: list[GroupShooter | None]

    @property
    def shooter_numbers(self) -> list[int | None]:
        """The 4 shooter numbers, None for a free slot (used by the edit popup)."""
        return [shooter.number if shooter else None for shooter in self.shooters]


def list_societies() -> list[Society]:
    """
    Get all the societies, sorted by name.

    Args :
        None

    Return :
        The list of societies (list[Society]), empty if there is none.
    """
    request = "SELECT id, name, location FROM societies ORDER BY name, location"
    try:
        rows = execute_request(request, ())
    except mariadb.Error:
        logger.exception("DB reading error on the societies table")
        raise

    return [
        Society(row[0], _society_label(row[0], row[1], row[2])) for row in rows or []
    ]


# One query joins the groups with the societies and with the shooters
# (LEFT JOIN : a group without society or with free slots is kept)
_GROUPS_QUERY: str = (
    "SELECT g.id, g.name, so.id, so.name, so.location, "
    "s1.shooter_number, s1.name, s2.shooter_number, s2.name, "
    "s3.shooter_number, s3.name, s4.shooter_number, s4.name "
    "FROM `groups` g "
    "LEFT JOIN societies so ON so.id = g.society_id "
    "LEFT JOIN shooters s1 ON s1.id = g.shooter_1 "
    "LEFT JOIN shooters s2 ON s2.id = g.shooter_2 "
    "LEFT JOIN shooters s3 ON s3.id = g.shooter_3 "
    "LEFT JOIN shooters s4 ON s4.id = g.shooter_4 "
)


def _build_group(row: list) -> Group:
    """
    Build a Group from a row of _GROUPS_QUERY.

    Args :
        row (list): the row (group, society, then 4 pairs shooter number / name).

    Return :
        The group (Group).
    """
    society = "" if row[2] is None else _society_label(row[2], row[3], row[4])

    # the shooters come as (number, name) pairs from the 6th column
    shooters: list[GroupShooter | None] = []
    for slot in range(4):
        number = row[5 + slot * 2]
        name = row[6 + slot * 2]
        shooters.append(None if number is None else GroupShooter(number, name))

    return Group(row[0], row[1] or "", row[2], society, shooters)


def _fetch_groups(where: str, params: tuple) -> list[Group]:
    """
    Run _GROUPS_QUERY with a filter and build the groups.

    Args :
        where (str): WHERE clause (with its "?" placeholders), or "" for no filter.
        params (tuple): values that replace the "?" placeholders.

    Return :
        The list of groups (list[Group]), sorted by id.
    """
    try:
        rows = execute_request(f"{_GROUPS_QUERY}{where} ORDER BY g.id", params)
    except mariadb.Error:
        logger.exception("DB reading error on the groups table")
        raise

    return [_build_group(row) for row in rows or []]


def list_groups() -> list[Group]:
    """
    Get all the groups with their society and their shooters.

    Args :
        None

    Return :
        The list of groups (list[Group]), sorted by id, empty if there is none.
    """
    return _fetch_groups("", ())


def get_group(group_id: int) -> Group | None:
    """
    Get one group with its society and its shooters.

    Args :
        group_id (int): id of the group.

    Return :
        The group (Group), or None if the id does not exist.
    """
    groups = _fetch_groups("WHERE g.id = ?", (group_id,))
    return groups[0] if groups else None


def group_exists(name: str, society_id: int, exclude_id: int = 0) -> bool:
    """
    Check if a group with this name already exists in this society.

    Args :
        name (str): name of the group.
        society_id (int): id of the society.
        exclude_id (int): id of a group to ignore (the group being edited).

    Return :
        True if the group exists (bool), else False.
    """
    request = (
        "SELECT 1 FROM `groups` WHERE name = ? AND society_id = ? AND id <> ? LIMIT 1"
    )
    try:
        rows = execute_request(request, (name, society_id, exclude_id))
    except mariadb.Error:
        logger.exception("DB reading error on the groups table")
        raise

    return bool(rows)


def count_group_programms(group_id: int) -> int:
    """
    Count the programms (shooting results) linked to a group.

    A group used by programms must not be deleted.

    Args :
        group_id (int): id of the group.

    Return :
        The number of programms of the group (int).
    """
    request = "SELECT COUNT(*) FROM programm WHERE group_id = ?"
    try:
        rows = execute_request(request, (group_id,))
    except mariadb.Error:
        logger.exception("DB reading error on the programm table")
        raise

    return int(rows[0][0]) if rows else 0


class SocietyDetail(NamedTuple):
    """A society with the number of shooters and groups that use it."""

    id: int
    name: str
    location: str
    shooter_count: int
    group_count: int

    @property
    def label(self) -> str:
        """The text shown for the society, for example "Tir Club (Lausanne)"."""
        return _society_label(self.id, self.name, self.location)


class ShooterRow(NamedTuple):
    """A row of the shooters table. The name is None until the listener receives it."""

    id: int
    number: int
    name: str | None
    society_id: int | None


# The counts are sub-queries : a society without shooter or group is kept
_SOCIETIES_QUERY: str = (
    "SELECT so.id, so.name, so.location, "
    "(SELECT COUNT(*) FROM shooters sh WHERE sh.society_id = so.id), "
    "(SELECT COUNT(*) FROM `groups` g WHERE g.society_id = so.id) "
    "FROM societies so "
)


def _fetch_societies(where: str, params: tuple) -> list[SocietyDetail]:
    """
    Run _SOCIETIES_QUERY with a filter and build the societies.

    Args :
        where (str): WHERE clause (with its "?" placeholders), or "" for no filter.
        params (tuple): values that replace the "?" placeholders.

    Return :
        The list of societies (list[SocietyDetail]), sorted by name.
    """
    request = f"{_SOCIETIES_QUERY}{where} ORDER BY so.name, so.location"
    try:
        rows = execute_request(request, params)
    except mariadb.Error:
        logger.exception("DB reading error on the societies table")
        raise

    return [
        SocietyDetail(row[0], row[1] or "", row[2] or "", int(row[3]), int(row[4]))
        for row in rows or []
    ]


def list_societies_detail() -> list[SocietyDetail]:
    """
    Get all the societies with their number of shooters and groups.

    Args :
        None

    Return :
        The list of societies (list[SocietyDetail]), empty if there is none.
    """
    return _fetch_societies("", ())


def get_society(society_id: int) -> SocietyDetail | None:
    """
    Get one society with its number of shooters and groups.

    Args :
        society_id (int): id of the society.

    Return :
        The society (SocietyDetail), or None if the id does not exist.
    """
    societies = _fetch_societies("WHERE so.id = ?", (society_id,))
    return societies[0] if societies else None


def society_exists(location: str, exclude_id: int = 0) -> bool:
    """
    Check if a society already exists at this location (the column is UNIQUE).

    Args :
        location (str): location of the society.
        exclude_id (int): id of a society to ignore (the society being edited).

    Return :
        True if the location is already used (bool), else False.
    """
    request = "SELECT 1 FROM societies WHERE location = ? AND id <> ? LIMIT 1"
    try:
        rows = execute_request(request, (location, exclude_id))
    except mariadb.Error:
        logger.exception("DB reading error on the societies table")
        raise

    return bool(rows)


def list_shooters() -> list[ShooterRow]:
    """
    Get all the shooters with their society id, sorted by shooter number.

    Args :
        None

    Return :
        The list of shooters (list[ShooterRow]), empty if there is none.
    """
    request = (
        "SELECT id, shooter_number, name, society_id FROM shooters "
        "ORDER BY shooter_number"
    )
    try:
        rows = execute_request(request, ())
    except mariadb.Error:
        logger.exception("DB reading error on the shooters table")
        raise

    return [ShooterRow(*row) for row in rows or []]


def format_time(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (time, datetime)):
        return value.strftime("%H:%M:%S")
    # texte du type "10:01:52.990000" ou "2026-11-08 10:01:52.990000"
    return str(value).split(".")[0].split(" ")[-1]


def listLastShot(target_number: int) -> list[tuple[float, float, int, int, str]]:
    _, serie_id = get_current(target_number)

    # get the info of the series
    request = "SELECT `show` FROM series WHERE id = ?"
    reponse = execute_request(request, (serie_id,))
    if reponse:
        result_seri = reponse[0]
    else:
        return []

    showed = result_seri[0]

    # Is the series is hidden (show=0), we return nothing
    if showed == 0:
        return []

    shots = getShotsBySeriesId(serie_id).get("shots")

    if not shots:
        return []

    return shots


def getShotsBySeriesId(serie_id) -> dict:
    """
    Retrieve all shots belonging to a series and aggregate series info.

    Parameters
    ----------
    serie_id : int
        Identifier of the series whose shots are requested.

    Returns
    -------
    dict
        A dictionary containing the series metadata (id, total scores, type,
        start and end times) and a list of tuples describing each shot:
        ``[(x, y, score_base10, score_base100, time_str), ...]``.  If the
        series does not exist or has no shots, an empty dictionary is
        returned.
    """
    # shots is [pos_x, pos_y, score_base10, score_base100, time]
    shots: list[tuple[float, float, int, int, str]] = []
    # Get the shots
    request_shots = (
        "SELECT s.x, s.y, s.score_base10, s.score_base100, s.time "
        "FROM shots s WHERE s.series_id = ? ORDER BY s.id DESC"
    )
    reponse = execute_request(request_shots, (serie_id,))

    if not reponse:
        return {}

    # Full iteration to process all results
    for row in reponse:
        shots.append(
            (
                float(row[0]),
                float(row[1]),
                int(row[2]),
                int(row[3]),
                format_time(row[4]),
            )
        )

    request_serie = (
        "SELECT se.score_base10, se.score_base100 , se.`type` , se.start_time , se.end_time "
        "FROM series se "
        "where se.id = ?;"
    )
    reponse = execute_request(request_serie, (serie_id,))

    if not reponse:
        return {}
    serie_info = reponse[0]

    return {
        "serie_id": serie_id,
        "total_base10": serie_info[0],
        "total_base100": serie_info[1],
        "type": serie_info[2],
        "start_time": format_time(serie_info[3]),
        "end_time": format_time(serie_info[4]),
        "shots": shots,
    }


def listScore(parent_id: int, type: str, max: int = 10) -> list[int]:
    """
    Return the list of scores for the shots or series belonging to a given parent.

    Parameters
    ----------
    parent_id : int
        Identifier of the parent (series or programme) whose scores are requested.
    type : str
        ``"shots"`` to fetch individual shot scores, ``"series"`` to fetch series
        scores.
    max : int, optional
        The scoring base to use; ``10`` or ``100`` are supported.

    Returns
    -------
    list[int]
        A list of integer scores, ordered from oldest to newest.  If no
        records exist, an empty list is returned.
    """

    scores: list[int] = []

    if type == "shots":
        parent_type = "series"
        child_type = "shots"
    elif type == "series":
        parent_type = "programm"
        child_type = "series"
    else:
        raise ValueError("Only the type shots or series are aviable.")

    if max == 10:
        shot_col = "score_base10"
    elif max == 100:
        shot_col = "score_base100"
    else:
        raise ValueError("the max can only be 10 or 100.")

    # request to get the lists of scores of the shots/series
    select_query = f"""
        SELECT child.{shot_col} FROM {child_type} child
        WHERE child.{parent_type}_id = ?;
        """
    reponse = execute_request(select_query, (parent_id,))

    if reponse:
        for row in reponse:
            if row[0] is not None:
                scores.append(int(row[0]))
            else:
                scores.append(0)

        return scores[::-1]
    else:
        return []


def getShooterNumberWithTarget(target_number: int) -> int | None:
    """
    Retrieve the shooter number associated with a target.

    Parameters
    ----------
    target_number : int
        Index of the target.

    Returns
    -------
    int | None
        The shooter's number, or ``None`` if the target has no associated
        programme.
    """
    programm_id, _ = get_current(target_number)

    request = "SELECT p.shooters_id FROM programm p WHERE p.id = ?;"

    reponse = execute_request(request, (programm_id,))

    if reponse:
        shooter_number = reponse[0][0]
        return shooter_number
    else:
        return None


def getShooterWithId(id: int) -> tuple[int, str] | None:
    """
    Fetch the shooter record by its primary key.

    Parameters
    ----------
    id : int
        Shooter primary key.

    Returns
    -------
    tuple[int, str] | None
        ``(shooter_number, name)`` if found, otherwise ``None``.
    """

    request = "SELECT s.shooter_number, s.name FROM shooters s WHERE s.id = ?;"

    reponse = execute_request(request, (id,))

    if reponse:
        shooter_number = int(reponse[0][0])
        name = str(reponse[0][1])
        return shooter_number, name
    else:
        return None


def getScoreSeriesOnTarget(target_number: int) -> int | None:
    """
    Return the total score of all shots in the current series for a target.

    The function fetches the current series using :func:`get_current` and
    then sums the ``score_base10`` values returned by :func:`listScore`.
    If the series does not exist, ``None`` is returned.
    """
    _, serie_id = get_current(target_number)

    if not serie_id:
        return None

    return sum(listScore(serie_id, "shots", 10))


def getTargetType(target_number: int) -> str:
    """
    Return the target type string for a target.

    The target type is stored in the ``programm`` table.  If the target
    has no associated programme, ``"A10"`` is returned as a default.
    """
    programm_id, _ = get_current(target_number)

    if not programm_id:
        return "A10"

    request = "SELECT p.target_type FROM programm p WHERE p.id = ?;"
    reponse = execute_request(request, (programm_id,))

    if reponse:
        target_type = reponse[0][0]
        return target_type
    else:
        return "A10"


def getAllShooters():
    """return all the shooter from the table shooters"""
    request = "SELECT * FROM shooters"
    reponse = execute_request(request, ())
    return reponse


def getAllDates():
    """Return all the programm.date distinct"""

    request = "SELECT DISTINCT p.date  FROM programm p"
    reponse = execute_request(request, ())
    return reponse


def getAllShots(shooter_id: int, date: str) -> list[int]:
    """Return all the shots from all the programm of a shooter"""
    request = (
        "select shots.score_base100, p.id "
        "from shooters s "
        "inner join programm p on p.shooters_id = s.id "
        "INNER JOIN series se on se.programm_id = p.id "
        "INNER JOIN shots on shots.series_id  = se.id "
        "where s.id = ? and p.`date` = ?;"
    )
    reponse = execute_request(request, (shooter_id, date))
    if reponse is None:
        return [0]

    shots: list[int] = []
    for shot in reponse:
        shots.append(int(shot[0]))

    return shots


def getAllProgramm(shooter_id, date: str) -> list[dict]:
    """
    Get all the programm from a shooter
    returning all the programm into a dict (json)

    Args :
        shooter_id (int): the id of the shooter

    Return :
        [{
            "id": int,
            "score_base10": int,
            "score_base100": int,
            "target_type": str,
            "start_time": str,
            "end_time": str,
        },
        {...}]
    """
    request = (
        "SELECT p.id, p.score_base10, p.score_base100, p.target_type, p.`date`, p.start_time, p.end_time "
        "FROM programm p "
        "WHERE p.shooters_id = ? and p.`date` = ?"
        "ORDER BY p.`date`, p.end_time DESC"
    )
    reponse = execute_request(request, (shooter_id, date))

    if not reponse:
        return [{}]
    try:
        list_programm: list[dict] = []
        for row in reponse:
            list_programm.append(
                {
                    "id": row[0],
                    "score_base10": row[1],
                    "score_base100": row[2],
                    "target_type": row[3],
                    "date": row[4],
                    "start_time": format_time(row[5]),
                    "end_time": format_time(row[6]),
                }
            )
    except TypeError:
        return [{}]
    return list_programm


def getProgrammById(id) -> dict:
    """
    Args:
        id (int): id of the programm
    Return :
        {
            start_time
            end_time
            score_base10
            score_base100
            target_number
            shooter:{
                id
                number
                name
            }
        }
    """
    request_programm = (
        "SELECT p.date, p.start_time, p.end_time, p.score_base10, p.score_base100, p.target_number, p.shooters_id "
        "FROM programm p "
        "WHERE p.id = ?;"
    )
    reponse = execute_request(request_programm, (id,))

    if not reponse:
        return {}

    (
        date,
        start_time,
        end_time,
        score_base10,
        score_base100,
        target_number,
        shooter_id,
    ) = reponse[0]
    shooter_info = getShooterWithId(shooter_id)

    if not shooter_info:
        return {}
    shooter_number, shooter_name = shooter_info

    return {
        "date": date,
        "start_time": format_time(start_time),
        "end_time": format_time(end_time),
        "score_base10": score_base10,
        "score_base100": score_base100,
        "target_number": target_number,
        "shooter": {"id": shooter_id, "number": shooter_number, "name": shooter_name},
    }


def getAllSeriesIdByProgrammId(programm_id) -> list[int]:
    """
    Retrieve all series identifiers belonging to a programme.

    Parameters
    ----------
    programm_id : int
        Identifier of the programme.

    Returns
    -------
    list[int]
        List of series IDs.  Returns an empty list if the programme
        has no series.
    """
    request = "select se.id from programm p inner join series se on se.programm_id = p.id where p.id = ?;"
    reponse = execute_request(request, (programm_id,))

    if not reponse:
        return []

    series_ids: list[int] = []
    for id in reponse:
        series_ids.append(int(id[0]))

    return series_ids


def getProgrammCountByTarget() -> dict:
    """
    Count the programms of each target for each day, formatted for a
    Chart.js grouped bar chart.

    Args :
        None

    Return :
        {
            "labels": list[str],  # x axis, one label per day
            "datasets": [
                {"label": str, "data": list[int]},  # one dataset per target
                ...
            ],
        }
        Both lists are empty if there is no programm or if the request fails.
    """

    request = (
        "SELECT p.target_number, p.`date` AS day_key, "
        "COUNT(p.id) AS number_of_programm "
        "FROM programm p "
        "GROUP BY p.target_number, p.`date` "
        "ORDER BY day_key, p.target_number;"
    )

    reponse = execute_request(request, ())

    if not reponse:
        return {"labels": [], "datasets": []}

    # pivot the rows into {day: {target: count}}
    # the dict keeps the order of the rows, already sorted by day in SQL
    counts: dict[str, dict[int, int]] = {}
    targets: set[int] = set()
    for target_number, day_key, number_of_programm in reponse:
        day = str(day_key) if day_key is not None else "unknown"
        counts.setdefault(day, {})[int(target_number)] = int(number_of_programm)
        targets.add(int(target_number))

    labels: list[str] = list(counts)

    # one dataset per target, 0 when the target had no programm that day
    # target_number is zero-based in the database, the display is one-based
    datasets: list[dict] = [
        {
            "label": f"Target {target + 1}",
            "data": [counts[day].get(target, 0) for day in labels],
        }
        for target in sorted(targets)
    ]

    return {"labels": labels, "datasets": datasets}
