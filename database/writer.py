# Title : database/Writer
# Author : Théo
# Last update : 27.10.2026
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
        args = (target_number, target_number)
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
        Returns the last inserted id if the option is enabled.

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
            if get_id:
                cursor.execute("SELECT LAST_INSERT_ID() AS inserted_id;")
                last_id_insered = cursor.fetchone()[0]
            else:
                last_id_insered = None
            conn.commit()
            return last_id_insered
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

    def start_programm(self, shooter_number: int, time: str, guid: str) -> None:
        insert_query = "INSERT INTO programm (shooters_number, taget_number, target_type, start_time, GUID) VALUES (?, ?, ?, ?, ?)"
        self.current_programm_id = self._execute_write(
            insert_query,
            (shooter_number, self.target_number, "A10", time, guid),
            get_id=True,
        )
        # update the current programm_id on the db
        update_query = """
        UPDATE `polytronic-target-display`.`current`
        SET programm_id = ?
        WHERE target_number = ?;
        """
        self._execute_write(
            update_query, (self.current_programm_id, self.target_number), get_id=False
        )

    def start_serie(self, serie_type: int, time: str, guid: str) -> None:
        insert_query = "INSERT INTO series (programm_id, type, start_time, `show`, GUID) VALUES (?, ?, ?, ?, ?)"
        showed = 0 if serie_type == 2 else 1

        self.current_serie_id = self._execute_write(
            insert_query,
            (self.current_programm_id, serie_type, time, showed, guid),
            get_id=True,
        )
        # update the current serie_id on the db
        update_query = """
        UPDATE `polytronic-target-display`.`current`
        SET series_id = ?
        WHERE target_number = ?;
        """
        self._execute_write(
            update_query, (self.current_serie_id, self.target_number), get_id=False
        )

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

    def programm_finish(self, time: str) -> None:
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
