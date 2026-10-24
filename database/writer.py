import mariadb

from database.connection import _get_connection


class InitTarget:
    """
    Gestionnaire d'état et d'écriture pour une cible spécifique.
    Chaque méthode ouvre sa propre connexion pour garantir la sécurité en parallèle.
    """

    def __init__(self, target_number: int) -> None:
        self.target_number = target_number
        self.current_programm_guid: str | None = None
        self.current_serie_guid: str | None = None

    def _execute_write(self, query: str, params: tuple) -> bool:
        """Helper interne pour exécuter une requête d'écriture avec gestion d'erreur."""
        conn = None
        cursor = None
        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except mariadb.IntegrityError as e:
            print(f"Erreur d'intégrité (doublon ?) : {e}")
            if conn:
                conn.rollback()
            return False
        except mariadb.Error as e:
            print(f"Erreur écriture DB : {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def start_programm(self, shooter_number: int, time: str, guid: str) -> None:
        self.current_programm_guid = guid
        insert_query = "INSERT INTO programm (shooters_number, taget_number,target_type, start_time, GUID) VALUES (?, ?, ?, ?)"
        self._execute_write(
            insert_query, (shooter_number, self.target_number, "A10", time, guid)
        )

    def start_serie(self, serie_type: int, time: str, guid: str) -> None:
        self.current_serie_guid = guid

        conn = None
        cursor = None
        programm_id = None

        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 1. Trouver l'ID du programme
            query = "SELECT id FROM programm WHERE GUID LIKE %s"
            cursor.execute(query, (f"%{self.current_programm_guid}%",))
            result = cursor.fetchone()

            if result:
                programm_id = result[0]
            else:
                print(
                    f"Aucun programme trouvé avec le GUID : {self.current_programm_guid}"
                )

            # 2. Préparer l'insertion
            showed = 0 if serie_type == 2 else 1
            insert_query = "INSERT INTO series (programm_id, type, start_time, `show`, GUID) VALUES (?, ?, ?, ?, ?)"

            # On réutilise le même curseur/connexion car on est dans le même bloc try
            cursor.execute(insert_query, (programm_id, serie_type, time, showed, guid))
            conn.commit()

        except mariadb.IntegrityError as e:
            print(f"Erreur intégrité série : {e}")
            if conn:
                conn.rollback()
        except mariadb.Error as e:
            print(f"Erreur écriture série : {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def serie_finish(self, time: str) -> None:
        from database.reader import listScore

        if not self.current_serie_guid:
            return
        update_query = "UPDATE series SET `show` = ?, score_base10 = ?, score_base100 = ?, end_time = ? WHERE GUID = ?"
        score_base10 = sum(listScore(self.current_serie_guid, "shots", max=10))
        score_base100 = sum(listScore(self.current_serie_guid, "shots", max=100))
        self._execute_write(
            update_query,
            (1, score_base10, score_base100, time, self.current_serie_guid),
        )

    def programm_finish(self, time: str) -> None:
        from database.reader import listScore

        if not self.current_programm_guid:
            return
        score_base10 = sum(listScore(self.current_programm_guid, "series", max=10))
        score_base100 = sum(listScore(self.current_programm_guid, "series", max=100))
        update_query = "UPDATE programm SET score_base10 = ?, score_base100 = ?, end_time = ? WHERE GUID = ?"
        self._execute_write(
            update_query,
            (score_base10, score_base100, time, self.current_programm_guid),
        )

    def shot(
        self,
        pos_x: float,
        pos_y: float,
        score_10: int,
        score_100: int,
        time: str,
        guid: str,
    ) -> None:
        if not self.current_serie_guid:
            print("Erreur: Tentative d'ajout de tir sans série active.")
            return

        conn = None
        cursor = None
        series_id = None

        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 1. Trouver l'ID de la série
            query = "SELECT id FROM series WHERE GUID LIKE %s"
            cursor.execute(query, (f"%{self.current_serie_guid}%",))
            result = cursor.fetchone()

            if result:
                series_id = result[0]
            else:
                print(f"Aucune série trouvée avec le GUID : {self.current_serie_guid}")
                return

            # 2. Insérer le tir
            insert_query = "INSERT INTO shots (x, y, time, score_base10, score_base100, series_id, GUID) VALUES (?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(
                insert_query, (pos_x, pos_y, time, score_10, score_100, series_id, guid)
            )
            conn.commit()

        except mariadb.IntegrityError as e:
            print(f"Erreur intégrité tir : {e}")
            if conn:
                conn.rollback()
        except mariadb.Error as e:
            print(f"Erreur écriture tir : {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
