# Title : Database
# Title: Database
# Author : Théo (Refactored by Euria)
# Author: Theo (Refactored by Euria)
# Last update : 17.09.2026
# Last update: 17.09.2026
# Description : Module for open the connection to the database.
# Description: Module for opening the connection to the database.

import logging
import os

import mariadb
from dotenv import load_dotenv

_ = load_dotenv()
logger = logging.getLogger(__name__)

# Creation of a pool
pool = mariadb.ConnectionPool(
    pool_name="mariadb_pool",
    pool_size=5,
    host=os.getenv("DATABASE_URL", "localhost"),
    port=int(os.getenv("DATABASE_PORT", "3306")),
    database=os.getenv("DATABASE_NAME", "polytronic-target-display"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    autocommit=False,
)


def _get_connection() -> mariadb.Connection:
    """Create and return a new connection to the mariadb database"""
    try:
        return pool.get_connection()
    except mariadb.Error as e:
        logger.fatal("Can't connect to the database !")
        print(f"Erreur de connexion à la base de données : {e}")
        raise


def execute_request(request: str, data: tuple) -> list[list] | None:
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
