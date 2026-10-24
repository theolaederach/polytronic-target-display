# Title : Database
# Author : Théo (Refactored by Euria)
# Last update : 17.09.2026
# Description : Module for open the connection to the database.

import os

import mariadb
from dotenv import load_dotenv

_ = load_dotenv()

port_str = os.getenv("DATABASE_PORT", "3306")
port = int(port_str)

db_config = {
    "host": os.getenv("DATABASE_URL"),
    "port": port,
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_NAME"),
    "autocommit": False,  # commit are gered manualy
}


def _get_connection() -> mariadb.Connection:
    """Create and return a new connection to the mariadb database"""
    try:
        return mariadb.connect(**db_config)
    except mariadb.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        raise


def execute_request(request: str, data: tuple) -> list | None:
    """
    Execute a sql request and return all rows as a list of tuples.

    Args:
        request (str): The SQL statement.  Use ``?`` as placeholder for parameters.
        data (tuple): The tuple of values that will replace the placeholders.

    Returns:
        list: of rows returned by ``SELECT``.
        None: for non‑SELECT statements (``INSERT``, ``UPDATE`` …).

    Raises:
        DatabaseError: Re‑raises any ``mariadb.Error`` with a richer context.
    """

    # Use context‑manager to ensure resources are freed
    with _get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(request, data)

        # Detect if the statement is a SELECT
        # ``cursor.description`` is *None* for non‑SELECT queries
        if cursor.description is None:
            return None

        # Fetch the data
        return cursor.fetchall()
