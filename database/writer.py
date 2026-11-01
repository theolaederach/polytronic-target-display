# Title : database/Writer
# Author : Théo
# Last update : 30.10.2026
# Description : Module for Write the data into the db
#               and manage the target with InitTarget()
import os

import mariadb

from database.connection import _get_connection, execute_request


class InitTarget:
    """
    State manager and writer for a specific target.
    """

    def __init__(self, target_number: int) -> None:
        """
        Initializes the target by setting the current program and series.
        """
        self.target_number = target_number
        self.current_programm_id: int | None
        self.current_serie_id: int | None

        # create the reference of the current target in the db
        query_set_current = """
        INSERT INTO `polytronic-target-display`.`current`
        (target_number, programm_id, series_id)
        SELECT ?, NULL, NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM `polytronic-target-display`.`current`
            WHERE `polytronic-target-display`.`current`.target_number = ?
        );
        """
        args = (self.target_number, self.target_number)
        self._execute_write(query_set_current, args)

        # get the current id of the programm and the series from the db
        self.update()

    def update(self) -> None:
        query_get_current_id = """
            SELECT c.programm_id, c.series_id
            FROM `polytronic-target-display`.`current` c
            WHERE c.target_number = ?;
        """
        currents_id = execute_request(query_get_current_id, (self.target_number,))
        if currents_id:
            for data in currents_id:
                self.current_programm_id = data[0]
                self.current_serie_id = data[1]

        else:
            self.current_programm_id = None
            self.current_serie_id = None

    def _execute_write(
        self, query: str, params: tuple, get_id: bool = False
    ) -> int | None:
        """
        Internal helper to execute a write query with error handling.

        Args:
            query (str): the SQL query to execute
            params (tuple): the values that replace "?" in the query.
            get_id (bool): return the id of the last insert query if True

        Returns:
            The id of the last insert query or None if get_id is False or an error occurs
        """
        conn = None
        cursor = None

        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if get_id:
                cursor.execute("SELECT LAST_INSERT_ID() AS inserted_id;")
                last_id_insered = cursor.fetchone()[0]
                return last_id_insered
            else:
                return None
        except mariadb.IntegrityError as e:
            print(f"Erreur d'intégrité (doublon ?) : {e}")
            if conn:
                conn.rollback()
            return None

        except mariadb.Error as e:
            print(f"Erreur écriture DB : {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def start_programm(
        self, shooter_number: int, time: str, guid: str, target_type: str = "A10"
    ) -> None:
        # The target type is not automaticlay set yet. to do later

        # force the programm to finish if a new begin
        self.programm_finish(time)

        insert_query = (
            "INSERT INTO programm (shooters_number, taget_number, target_type, "
            "start_time, GUID) VALUES (?, ?, ?, ?, ?)"
        )
        new_id = self._execute_write(
            insert_query,
            (shooter_number, self.target_number, target_type, time, guid),
            get_id=True,
        )

        if new_id is None:
            # INSERT failed (duplicate GUID, DB down...) : keep the previous state
            print(
                f"Erreur : programme non enregistré (cible {self.target_number}, "
                f"guid {guid}), état précédent conservé."
            )
            return

        self.current_programm_id = new_id

        # update the current programm_id on the db
        update_query = """
        UPDATE `polytronic-target-display`.`current`
        SET programm_id = ?
        WHERE target_number = ?;
        """
        self._execute_write(update_query, (new_id, self.target_number))

    def start_serie(self, serie_type: int, time: str, guid: str) -> None:
        # Force the last serie to finish if a new begin
        self.serie_finish(time)

        insert_query = (
            "INSERT INTO series (programm_id, type, start_time, "
            "`show`, GUID) VALUES (?, ?, ?, ?, ?)"
        )
        showed = 0 if serie_type == 2 else 1

        new_id = self._execute_write(
            insert_query,
            (self.current_serie_id, serie_type, time, showed, guid),
            get_id=True,
        )

        update_query = """
        UPDATE `polytronic-target-display`.`current`
        SET series_id = ?
        WHERE target_number = ?;
        """

        if new_id is None:
            # INSERT failed (duplicate GUID, DB down...) : keep the previous state
            print(
                f"Erreur : serie non enregistré (cible {self.target_number}, "
                f"guid {guid}), état précédent conservé."
            )
            # update the current serie id ans et it to None
            self._execute_write(update_query, (None, self.target_number))
            return

        self.current_serie_id = new_id

        # update the current serie id on the db
        self._execute_write(update_query, (new_id, self.target_number))

    def serie_finish(self, time: str) -> None:
        from database.reader import listScore

        if not self.current_serie_id:
            return
        update_query = "UPDATE series SET `show` = ?, score_base10 = ?, score_base100 = ?, end_time = ? WHERE id = ?"
        score_base10 = sum(listScore(self.current_serie_id, "shots", max=10))
        score_base100 = sum(listScore(self.current_serie_id, "shots", max=100))
        self._execute_write(
            update_query,
            (1, score_base10, score_base100, time, self.current_serie_id),
        )

    def programm_finish(self, time) -> None:
        from database.reader import listScore

        if not self.current_programm_id:
            return
        score_base10 = sum(listScore(self.current_programm_id, "series", max=10))
        score_base100 = sum(listScore(self.current_programm_id, "series", max=100))
        update_query = "UPDATE programm SET score_base10 = ?, score_base100 = ?, end_time = ? WHERE id = ?"
        self._execute_write(
            update_query,
            (score_base10, score_base100, time, self.current_programm_id),
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
        if not self.current_serie_id:
            print("Erreur: Tentative d'ajout de tir sans série active.")
            return

        insert_query = "INSERT INTO shots (x, y, time, score_base10, score_base100, series_id, GUID) VALUES (?, ?, ?, ?, ?, ?, ?)"
        self._execute_write(
            insert_query,
            (pos_x, pos_y, time, score_10, score_100, self.current_serie_id, guid),
        )


# List of targets
targets: list[InitTarget] = []

numberOfTarget_str = os.getenv("NumberOfTarget", "5")
numberOfTarget = int(numberOfTarget_str)

for target in range(numberOfTarget):
    targets.insert(target, InitTarget(target))
