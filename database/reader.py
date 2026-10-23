"""
This file only call the read function, like readShots
"""

import mariadb

from database.connection import _get_connection, targets


def listLastShot(target_number: int) -> list[tuple[float, float, int]]:
    """Lit les tirs d'une cible spécifique de manière isolée."""

    # Vérification de l'existence de la cible dans la liste globale
    try:
        current_guid = targets[target_number].current_serie_guid
    except (IndexError, AttributeError):
        print(f"Attention : Cible {target_number} non initialisée ou introuvable.")
        return []

    if not current_guid:
        return []

    conn = None
    cursor = None
    shots: list[tuple[float, float, int]] = []

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # 1. Récupérer les infos de la série
        query_prog = "SELECT id, `show` FROM series WHERE GUID LIKE %s"
        cursor.execute(query_prog, (current_guid,))
        result_seri = cursor.fetchone()

        if not result_seri:
            # Pas critique, la série n'existe peut-être pas encore
            return []

        serie_id = int(result_seri[0])
        showed = result_seri[1]

        # Si la série est cachée (show=0), on ne renvoie rien
        if showed == 0:
            return []

        # 2. Récupérer les tirs
        select_query = "SELECT x, y,score_base100 FROM shots WHERE series_id = %s"
        cursor.execute(select_query, (serie_id,))

        # Itération complète pour consommer tous les résultats
        for row in cursor:
            shots.append((float(row[0]), float(row[1]), int(row[2])))

        return shots[::-1]

    except mariadb.Error as e:
        print(f"Erreur lecture DB (Cible {target_number}) : {e}")
        return []
    except Exception as e:
        print(f"Erreur inattendue lecture (Cible {target_number}) : {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def listScore(guid: str, type: str, max: int = 10) -> list[int]:
    """
    this function return all the shots's scrores of a series.
    you can only user guid or target_number, not both of theme.

    Args:
        guid (str): the guid of the series/programm
        type (str): shots/series
        max (int): max of the scores. 10/100 is the only value aviable
    """

    conn = None
    cursor = None
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

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # select_query = "SELECT sh.score_base100 FROM shots sh inner join series se on se.id = sh.series_id WHERE se.GUID = %s;"
        # request to get the lists of scores of the shots/series
        select_query = (
            f"SELECT child.{shot_col} FROM {child_type} child "
            f"inner join {parent_type} parent on parent.id = child.{parent_type}_id "
            f"WHERE parent.GUID = %s;"
        )
        cursor.execute(select_query, (guid,))

        for row in cursor:
            if row[0] is not None:
                scores.append(int(row[0]))
            else:
                scores.append(0)

        return scores[::-1]

    except mariadb.Error as e:
        print(f"Erreur lecture DB (serie guid : {guid}) : {e}")
        return [0]
    except Exception as e:
        print(f"Erreur inattendue lecture (Cible {guid}) : {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
