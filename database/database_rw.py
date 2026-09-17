# Title : Database
# Author : Théo
# Last update : 15.09.2026
# Description : Module for read and manage the data from the database

import os

import mariadb
from dotenv import load_dotenv

_ = load_dotenv()

port_str = os.getenv("DATABASE_PORT", "3306")

# la convertir en int
port = int(port_str)

db_config = {
    "host": os.getenv("DATABASE_URL"),
    "port": port,
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_NAME"),
}


try:
    print("Connecting to MariaDB...")
    conn = mariadb.connect(**db_config)
    print("Connection successful!")

    cursor = conn.cursor()

except mariadb.Error as e:
    print("Something goes wrong with the database .", e)


def readShot(shooter: int) -> list[tuple[float, float]]:
    select_query = "SELECT x, y FROM shots WHERE shooters_number LIKE ? LIMIT 10"

    cursor.execute(select_query, (f"%{shooter}%",))

    shots: list[tuple[float, float]] = []

    for row in cursor:
        shots.append((row[0], row[1]))

    return shots


class InitTarget:
    """
    Initialisation of  target

    Attributes
    ----------
    target_number : int
        Identifier of the target being fired at.

    Example
    -------
    >>> target = (1)

    >>> target.start_programm(shooter_number=1723,
    ...                     time="12:14:09.24", guid="2199094003")
    >>> target.serie_begin(serie_type=1, time="12:14:09.24", guid="2199094003")
    >>> target.shot(pos_x=-0.15586710, pos_y=0.04704675,
                            score_10=7, score_100=69, guid="2199094003")
    >>> target.serie_finish("12:14:09.24")
    """

    def __init__(self, target_number: int) -> None:
        self.target_number = target_number
        self.temp_programm = None
        self.temp_serie = None

    def start_programm(self, shooter_number: int, time: str, guid: str) -> None:
        """
        Begin of a shooting programm to track the begin and
        the end of a series.

        Parameters
        ----------
        shooter_number : int
            Identifier of the shooter.
        time : str
            time in HH:mm:ss.ms (e.g., "12:14:09.24").
        guid : str
            Universally‑unique identifier for the program.
        """

        self.temp_programm = guid

        insert_query = (
            "INSERT INTO programm (shooters_number, taget_number, start_time, GUID) VALUES (?, ?, ?, ?)"
        )
        try:
            cursor.execute(insert_query, (shooter_number,self.target_number, time, guid))
            conn.commit()
        except mariadb.IntegrityError as e:
            print(f"Error inserting data in programm (might be duplicate GUID): {e}")
            conn.rollback()
        except mariadb.Error as e:
            print(f"Error inserting data in programm: {e}")
            conn.rollback()

    def start_serie(self, serie_type: int, time: str, guid: str) -> None:
        """
        Signal the start of a series. (_GRPH)

        Parameters
        ----------
        serie_type : int
            Type code of the series (e.g., 0 = trial, 1= shot by shot,2 = hidden shots, ).
        time : str
            time in HH:mm:ss.ms (e.g., "12:14:09.24").
        guid : str
            Same program GUID – useful for logging or correlation.
        """

        self.temp_serie = guid
        # 1. Correction du marqueur (%s au lieu de ?)
        query = "SELECT id FROM programm WHERE GUID LIKE %s"
        params = (f"%{self.temp_programm}%",)

        cursor.execute(query, params)

        # 2. Récupération du résultat
        result = cursor.fetchone()

        if result:
            # Extraction de la valeur hors du tuple (ex: (123,) -> 123)
            programm_id = result[0]
        else:
            print(f"Any programm found with the GUID : {self.temp_programm}")

            programm_id = None

        insert_query = "INSERT INTO series (programm_id, type, start_time, `show`, GUID) VALUES (?, ?, ?, ?, ?)"
        try:
            cursor.execute(insert_query, (programm_id, serie_type, time, 0, guid))
            conn.commit()
        except mariadb.IntegrityError as e:
            print(f"Error inserting data in series (might be duplicate GUID): {e}")
            conn.rollback()
        except mariadb.Error as e:
            print(f"Error inserting data in series: {e}")
            conn.rollback()

    def serie_finish(self, time: str) -> None:
        """
        Signal the end of the current series. (_SUBT)

        Parameters
        ----------
        time : str
             time in HH:mm:ss.ms (e.g., "12:14:09.24").
        """

        update_query = "UPDATE series SET end_time = ?, `show` = ? WHERE GUID = ?"
        cursor.execute(update_query, (time, 1, self.temp_serie))
        conn.commit()

    def programm_finish(self) -> None:
        """
        Signal the end of the current programm. (_PRST)

        Parameters
        ----------
        time : str
             time in HH:mm:ss.ms (e.g., "12:14:09.24").
        """

        update_query = "UPDATE programm SET total_final_base10 = ?, total_final_base100 = ? WHERE GUID = ?"
        cursor.execute(update_query, (10, 100, self.temp_programm))
        conn.commit()

    def shot(
        self,
        pos_x: float,
        pos_y: float,
        score_10: int,
        score_100: int,
        time: str,
        guid: str,
    ) -> None:
        """
        Record a single shot.

        Parameters
        ----------
        pos_x, pos_y : float
            Coordinate in put impact on the target
        score_10 : int
            Score out of 10 .
        score_100 : int
            Score out of 100.
        guid : str
            Same program GUID – for traceability.
        """

        query = "SELECT id FROM series WHERE GUID LIKE %s"
        params = (f"%{self.temp_serie}%",)

        cursor.execute(query, params)

        result = cursor.fetchone()

        if result:
            # Extract of the value (ex: (123,) -> 123)
            series_id = result[0]
        else:
            print(f"Any series found with the GUID : {self.temp_serie}")
            series_id = None

        insert_query = "INSERT INTO shots (x, y, time, score_base10, score_base100, series_id, GUID) VALUES (?, ?, ?, ?, ?, ?, ?)"
        try:
            cursor.execute(
                insert_query, (pos_x, pos_y, time, score_10, score_100, series_id, guid)
            )
            conn.commit()
        except mariadb.IntegrityError as e:
            print(f"Error inserting data in shots (might be duplicate GUID): {e}")
            conn.rollback()
        except mariadb.Error as e:
            print(f"Error inserting data in shots (GUID : {guid}, x : {pos_x}, y={pos_y}): {e}")
            conn.rollback()
