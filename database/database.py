# Title : Database
# Author : Théo
# Last update : 31.08.2026
# Description : Module for read and manage the data from the database

import os

import mariadb
from dotenv import load_dotenv

_ = load_dotenv()

db_config = {
    "host": os.getenv("DATABASE_URL"),
    "port": 3306,
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
