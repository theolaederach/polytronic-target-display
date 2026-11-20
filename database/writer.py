# Title : database/Writer
# Author : Théo
# Last update : 30.10.2026
# Description : Module for Write the data into the db
#               and manage the target with InitTarget()
import logging
import os
from datetime import date

import mariadb

logger = logging.getLogger(__name__)

from database.connection import _get_connection, execute_request


def get_current(target_number: int) -> tuple[int | None, int | None]:
    """Return (programm_id, series_id) of the target, read from the db."""
    rows = execute_request(
        "SELECT programm_id, series_id FROM current WHERE target_number = ?",
        (target_number,),
    )
    return (rows[0][0], rows[0][1]) if rows else (None, None)


def getShooterByNumber(shooter_number: int) -> tuple[int, str]:
    request = "SELECT s.id, s.name from shooters s WHERE  s.shooter_number = ?;"

    result = execute_request(request, (shooter_number,))
    if result:
        try:
            id = int(result[0][0])
            name = result[0][1]
            return (id, name)
        except TypeError:
            return (0, "???")
    else:
        return (0, "???")


def create_user(username: str, password_hash: str, role: str = "admin") -> int | None:
    """
    Insert a new user in the users table.

    Args :
        username (str): unique login name.
        password_hash (str): hash of the password (never the clear password).
        role (str): role of the user, "admin" by default.

    Return :
        The id of the new user (int), or None if the insert failed
        (for example if the username already exists).
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            new_id: int | None = cursor.lastrowid
        # the pool uses autocommit=False : the insert must be committed
        conn.commit()
        return new_id

    except mariadb.IntegrityError:
        logger.error("User '%s' already exists", username)
        if conn:
            conn.rollback()
        return None

    except mariadb.Error:
        logger.exception("DB writing error (create_user)")
        if conn:
            conn.rollback()
        return None

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def _get_shooter_ids(
    cursor: "mariadb.Cursor", society_id: int, shooter_numbers: list[int]
) -> list[int | None]:
    """
    Get the id of each shooter number, and create the unknown shooters.

    A shooter number that is not in the shooters table yet is created without
    name (the listener fills the name when the shooter appears on a target).

    Args :
        cursor (mariadb.Cursor): cursor of the transaction in progress.
        society_id (int): id of the society, given to the shooters it creates.
        shooter_numbers (list[int]): shooter numbers (1 to 4).

    Return :
        The 4 shooter ids (list), in the order of the numbers.
        Free slots are None.
    """
    shooter_ids: list[int | None] = []

    for number in shooter_numbers:
        cursor.execute("SELECT id FROM shooters WHERE shooter_number = ?", (number,))
        row = cursor.fetchone()

        if row is None:
            # unknown shooter : create it in the society of the group
            cursor.execute(
                "INSERT INTO shooters (shooter_number, society_id) VALUES (?, ?)",
                (number, society_id),
            )
            shooter_ids.append(cursor.lastrowid)
        else:
            shooter_ids.append(row[0])

    # free slots stay NULL
    return shooter_ids + [None] * (4 - len(shooter_ids))


def create_group(
    name: str, society_id: int, shooter_numbers: list[int]
) -> int | None:
    """
    Insert a new group with its shooters, in one transaction.

    The shooters are stored in the first free slots (shooter_1, shooter_2...).

    Args :
        name (str): name of the group.
        society_id (int): id of the society of the group.
        shooter_numbers (list[int]): shooter numbers (1 to 4, no duplicate).

    Return :
        The id of the new group (int), or None if the insert failed.
    """
    if not 1 <= len(shooter_numbers) <= 4:
        logger.error("A group needs 1 to 4 shooters, got %d", len(shooter_numbers))
        return None

    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            shooter_ids = _get_shooter_ids(cursor, society_id, shooter_numbers)

            cursor.execute(
                "INSERT INTO `groups` "
                "(name, society_id, shooter_1, shooter_2, shooter_3, shooter_4) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, society_id, *shooter_ids),
            )
            group_id: int | None = cursor.lastrowid

        # shooters and group are saved together, or not at all
        conn.commit()
        return group_id

    except mariadb.Error:
        logger.exception("DB writing error (create_group)")
        if conn:
            conn.rollback()
        return None

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def update_group(
    group_id: int, name: str, society_id: int, shooter_numbers: list[int]
) -> bool:
    """
    Change the name, the society and the shooters of a group, in one transaction.

    The shooters are stored in the first free slots (shooter_1, shooter_2...).
    The shooters removed from the group are kept in the shooters table.

    Args :
        group_id (int): id of the group to change.
        name (str): new name of the group.
        society_id (int): id of the new society of the group.
        shooter_numbers (list[int]): shooter numbers (1 to 4, no duplicate).

    Return :
        True if the group was saved (bool), False if the update failed.
    """
    if not 1 <= len(shooter_numbers) <= 4:
        logger.error("A group needs 1 to 4 shooters, got %d", len(shooter_numbers))
        return False

    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            shooter_ids = _get_shooter_ids(cursor, society_id, shooter_numbers)

            cursor.execute(
                "UPDATE `groups` SET name = ?, society_id = ?, "
                "shooter_1 = ?, shooter_2 = ?, shooter_3 = ?, shooter_4 = ? "
                "WHERE id = ?",
                (name, society_id, *shooter_ids, group_id),
            )

        # shooters and group are saved together, or not at all
        conn.commit()
        return True

    except mariadb.Error:
        logger.exception("DB writing error (update_group)")
        if conn:
            conn.rollback()
        return False

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def delete_group(group_id: int) -> bool:
    """
    Delete a group. The shooters of the group are kept.

    The database refuses to delete a group that is used by a programm
    (foreign key) : check count_group_programms() before.

    Args :
        group_id (int): id of the group to delete.

    Return :
        True if the group was deleted (bool), False if the delete failed.
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM `groups` WHERE id = ?", (group_id,))

        conn.commit()
        return True

    except mariadb.Error:
        logger.exception("DB writing error (delete_group)")
        if conn:
            conn.rollback()
        return False

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def create_society(name: str, location: str) -> int | None:
    """
    Insert a new society.

    Args :
        name (str): name of the society.
        location (str): location of the society (must be unique).

    Return :
        The id of the new society (int), or None if the insert failed.
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO societies (name, location) VALUES (?, ?)",
                (name, location),
            )
            society_id: int | None = cursor.lastrowid

        conn.commit()
        return society_id

    except mariadb.Error:
        logger.exception("DB writing error (create_society)")
        if conn:
            conn.rollback()
        return None

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def update_society(society_id: int, name: str, location: str) -> bool:
    """
    Change the name and the location of a society.

    Args :
        society_id (int): id of the society to change.
        name (str): new name of the society.
        location (str): new location of the society (must be unique).

    Return :
        True if the society was saved (bool), False if the update failed.
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE societies SET name = ?, location = ? WHERE id = ?",
                (name, location, society_id),
            )

        conn.commit()
        return True

    except mariadb.Error:
        logger.exception("DB writing error (update_society)")
        if conn:
            conn.rollback()
        return False

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def delete_society(society_id: int) -> bool:
    """
    Delete a society. Its shooters are kept, without society.

    The database refuses to delete a society that is used by a group
    (foreign key) : check the group count before.

    Args :
        society_id (int): id of the society to delete.

    Return :
        True if the society was deleted (bool), False if the delete failed.
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            # detach the shooters first, the foreign key would refuse the delete
            cursor.execute(
                "UPDATE shooters SET society_id = NULL WHERE society_id = ?",
                (society_id,),
            )
            cursor.execute("DELETE FROM societies WHERE id = ?", (society_id,))

        # detach and delete are saved together, or not at all
        conn.commit()
        return True

    except mariadb.Error:
        logger.exception("DB writing error (delete_society)")
        if conn:
            conn.rollback()
        return False

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


def set_shooters_society(assignments: dict[int, int | None]) -> bool:
    """
    Change the society of several shooters, in one transaction.

    Args :
        assignments (dict[int, int | None]): society id (None for no society)
            by shooter id (the id of the table, not the shooter number).

    Return :
        True if all the shooters were saved (bool), False if the update failed.
    """
    conn: mariadb.Connection | None = None

    try:
        conn = _get_connection()
        with conn.cursor() as cursor:
            for shooter_id, society_id in assignments.items():
                cursor.execute(
                    "UPDATE shooters SET society_id = ? WHERE id = ?",
                    (society_id, shooter_id),
                )

        # all the shooters are saved together, or none
        conn.commit()
        return True

    except mariadb.Error:
        logger.exception("DB writing error (set_shooters_society)")
        if conn:
            conn.rollback()
        return False

    finally:
        # give the connection back to the pool
        if conn:
            conn.close()


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
        query_set_current = (
            "INSERT INTO `current` "
            "(target_number, programm_id, series_id) "
            "SELECT ?, NULL, NULL "
            "WHERE NOT EXISTS ( "
            "    SELECT 1 FROM `current` "
            "    WHERE `current`.target_number = ?);"
        )
        args = (self.target_number, self.target_number)
        self._execute_write(query_set_current, args)

        # get the current id of the programm and the series from the db
        self._update()

    def _update(self) -> None:
        query_get_current_id = (
            "SELECT c.programm_id, c.series_id "
            "FROM `current` c "
            "WHERE c.target_number = ?;"
        )
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

        except mariadb.IntegrityError:
            logger.error(
                "DB writing error (duplicate ?) (query=%s, args=%s)", query[:40], params
            )
            if conn:
                conn.rollback()
            return None

        except mariadb.Error:
            logger.exception("DB writing error (query=%s)", query[:40])
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def write_shooter(self, shooter_number: int, shooter_name: str) -> None:
        """
        Create a new shooter related to his shooter number with his name,
        or edit his name if the value from the listener change.
        """
        insert_query = (
            "INSERT INTO `polytronic-target-display`.shooters (shooter_number, name) "
            "VALUES (?, ?) "
            "ON DUPLICATE KEY UPDATE "
            "    name = VALUES(name);"
        )

        _ = self._execute_write(insert_query, (shooter_number, shooter_name))

    def start_programm(
        self, shooter_number: int, time: str, guid: str, target_type: str = "A10"
    ) -> None:
        # The target type is not automaticlay set yet. to do later

        # force the programm to finish if a new begin
        self.programm_finish(time)

        insert_query = (
            "INSERT INTO programm (shooters_id, target_number, target_type, "
            "start_time, `date`, GUID) VALUES (?, ?, ?, ?, ?, ?)"
        )
        shooter_id, _ = getShooterByNumber(shooter_number)
        current_date = date.today()
        new_id = self._execute_write(
            insert_query,
            (shooter_id, self.target_number, target_type, time, current_date, guid),
            get_id=True,
        )

        if new_id is None:
            # INSERT failed (duplicate GUID, DB down...) : keep the previous state
            logger.error(
                "Programm not save (target %r, programm guid : %r)",
                self.target_number,
                guid,
            )
            return

        self.current_programm_id = new_id

        # update the current programm_id on the db
        update_query = "UPDATE `current`SET programm_id = ? WHERE target_number = ?;"
        self._execute_write(update_query, (new_id, self.target_number))

    def start_serie(self, serie_type: int, time: str, guid: str) -> None:
        # Force the last serie to finish if a new begin
        self.serie_finish(time)

        programm_id, _ = get_current(self.target_number)
        if programm_id is None:
            logger.error(
                "Serie without active programm (target %r)", self.target_number
            )
            return

        insert_query = (
            "INSERT INTO series (programm_id, type, start_time, "
            "`show`, GUID) VALUES (?, ?, ?, ?, ?)"
        )
        showed = 0 if serie_type == 2 else 1

        new_id = self._execute_write(
            insert_query,
            (programm_id, serie_type, time, showed, guid),
            get_id=True,
        )

        update_query = "UPDATE `current`SET series_id = ? WHERE target_number = ?;"

        if new_id is None:
            # INSERT failed (duplicate GUID, DB down...) : keep the previous state
            logger.error(
                "Serie not save (target %r, serie guid : %r",
                self.target_number,
                guid,
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
        update_query = (
            "UPDATE series SET `show` = ?, "
            "score_base10 = ?, score_base100 = ?, end_time = ? WHERE id = ?"
        )
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
        update_query = (
            "UPDATE programm SET score_base10 = ?, "
            "score_base100 = ?, end_time = ? WHERE id = ?"
        )
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
        _, serie_id = get_current(self.target_number)
        if serie_id is None:
            logger.error(
                "unable to insert a shot without active serie. (target %r)",
                self.target_number,
            )
            return

        insert_query = (
            "INSERT INTO shots (x, y, time, score_base10, score_base100, series_id, GUID) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        self._execute_write(
            insert_query,
            (pos_x, pos_y, time, score_10, score_100, serie_id, guid),
        )


# List of targets
targets: list[InitTarget] = []

numberOfTarget_str = os.getenv("NumberOfTarget", "5")
numberOfTarget = int(numberOfTarget_str)

for target in range(numberOfTarget):
    targets.insert(target, InitTarget(target))
