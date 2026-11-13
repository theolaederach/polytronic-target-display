# Title : database/reader
# Author : Théo
# Last update : 27.10.2026
# Description : Module for read the database with function like listScore()

from datetime import datetime, time

from werkzeug.datastructures.structures import TypeConversionDict

from database.connection import execute_request
from database.writer import get_current


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
