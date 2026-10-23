"""
This file only call the read function, like readShots
"""

import mariadb
from connection import _get_connection, targets


def readShot(target_number: int) -> list[tuple[float, float, int]]:
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

        if not shots:
            # Optionnel : loguer si besoin
            pass

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
