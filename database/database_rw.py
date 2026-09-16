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
    Begin of a shooting programm to track the begin and
    the end of a series.


    Attributes
    ----------
    target_number : int
        Identifier of the target being fired at.
    shooter_number : int
        Identifier of the shooter.
    time : int
        Unix timestamp of the program start (seconds since epoch).
    guid : str
        Universally‑unique identifier for the program.

    Example
    -------
    >>> prog = StartProgram(target_number=3, shooter_number=1723,
    ...                     time="12:14:09.24", guid="2199094003")
    >>> prog.serie_begin(serie_type=1, time="12:14:09.24", guid="2199094003")
    >>> prog.shot(pos_x=-0.15586710, pos_y=0.04704675,
                            score_10=7, score_100=69, guid="2199094003")
    >>> prog.serie_finish("12:14:09.24")
    """
    def __init__(self, target_number: int) -> None:
        self.target_number = target_number


    def start_programm(self, shooter_number: int, time: str,
        guid: str) -> None:

        print(f"[START] Program {guid} for target {self.target_number} (shooter {shooter_number})")

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
        print(f"[SERIE BEGIN] {time} – Type {serie_type} on target {self.target_number}")

    def serie_finish(self, time: str) -> None:
        """
        Signal the end of the current series. (_SUBT)

        Parameters
        ----------
        time : str
             time in HH:mm:ss.ms (e.g., "12:14:09.24").
        """
        print(f"[SERIE END] {time} – Target {self.target_number}")

    def programm_finish(self, time: str) -> None:
        """
        Signal the end of the current programm. (_PRST)

        Parameters
        ----------
        time : str
             time in HH:mm:ss.ms (e.g., "12:14:09.24").
        """
        print(f"[PROGRAMM END] {time} – Target {self.target_number}")


    def shot(self, pos_x: float, pos_y: float,
             score_10: int, score_100: int,
             time : str, guid: str) -> None:
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
        print(f"[SHOT] {guid} – Target {self.target_number} "
              f"pos=({pos_x:.2f},{pos_y:.2f}) "
              f"score10={score_10} score100={score_100}")
