"""
This file only call the read function, like readShots
"""

from database.connection import execute_request
from database.writer import targets


def listLastShot(target_number: int) -> list[tuple[float, float, int]]:
    """
    Reads the shots of a series of a single taget

    (to do later, i'm too busy now)
    """

    # Checking Whether the Target Exists in the Global List
    try:
        current_guid = targets[target_number].current_serie_guid
    except (IndexError, AttributeError):
        print(f"Waring : Target {target_number} uninitialised or not found.")
        return []

    if not current_guid:
        return []

    shots: list[tuple[float, float, int]] = []

    # get the info of the series
    request = "SELECT id, `show` FROM series WHERE GUID LIKE ?"
    reponse = execute_request(request, (current_guid,))
    if reponse:
        result_seri = reponse[0]
    else:
        return []

    serie_id = int(result_seri[0])
    showed = result_seri[1]

    # Is the series is hidden (show=0), we return nothing
    if showed == 0:
        return []

    # Get the shots
    request = "SELECT x, y,score_base100 FROM shots WHERE series_id = ?"
    reponse = execute_request(request, (serie_id,))

    if reponse:
        # Full iteration to process all results
        for row in reponse:
            shots.append((float(row[0]), float(row[1]), int(row[2])))

        return shots[::-1]
    else:
        return []


def listScore(guid: str, type: str, max: int = 10) -> list[int]:
    """
    this function return all the shots's scrores of a series.
    you can only user guid or target_number, not both of theme.

    Args:
        guid (str): the guid of the series/programm
        type (str): shots/series
        max (int): max of the scores. 10/100 is the only value aviable

    Return (list[int]): the list of the shots or series's score.
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
    select_query = (
        f"SELECT child.{shot_col} FROM {child_type} child "
        f"inner join {parent_type} parent on parent.id = child.{parent_type}_id "
        f"WHERE parent.GUID = ?;"
    )
    reponse = execute_request(select_query, (guid,))

    if reponse:
        for row in reponse:
            if row[0] is not None:
                scores.append(int(row[0]))
            else:
                scores.append(0)

        return scores[::-1]
    else:
        return []


def getShooterNumber(target_number: int) -> int | None:

    programm_guid = targets[target_number].current_programm_guid
    request = "SELECT p.shooters_number FROM programm p WHERE p.GUID = ?;"

    reponse = execute_request(request, (programm_guid,))

    if reponse:
        shooter_number = reponse[0][0]
        return shooter_number
    else:
        return None


def getScoreSeriesOnTarget(target_number: int) -> int | None:
    """
    Function description :
    To do later too, i'm still too busy
    """
    try:
        serie_guid = targets[target_number].current_serie_guid
    except (IndexError, AttributeError):
        print(f"Waring : Target {target_number} uninitialised or not found.")
        return None

    if not serie_guid:
        return None

    return sum(listScore(serie_guid, "shots", 10))


def getTargetType(target_number: int) -> str:
    """
    Function description :
    To do later too, i'm still too busy
    """
    try:
        programm_guid = targets[target_number].current_programm_guid
    except (IndexError, AttributeError):
        print(f"Waring : Target {target_number} uninitialised or not found.")
        return "A10"

    if not programm_guid:
        return "A10"

    request = "SELECT p.target_type FROM programm p WHERE p.GUID = ?;"
    reponse = execute_request(request, (programm_guid,))

    if reponse:
        target_type = reponse[0][0]
        return target_type
    else:
        return "A10"
