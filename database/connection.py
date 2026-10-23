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
    "autocommit": False, # commit are gered manualy
}

# List of targets (init by the listener)
targets = []


def _get_connection() -> mariadb.Connection:
    """Create and return a new connection to the mariadb database"""
    try:
        return mariadb.connect(**db_config)
    except mariadb.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        raise


