# Title : Database
# Author : Théo
# Last update : 31.08.2026
# Description : Module for read and manage the data from the database

from logging import exception

from dotenv import load_dotenv
import mariadb
import os
import sys

_ = load_dotenv()

db_config = {
    'host': os.getenv('DATABASE_URL'),
    'port': 3306,
    'user': os.getenv('DATABASE_USER'),
    'password': os.getenv('DATABASE_PASSWORD'),
    'database': os.getenv('DATABASE_NAME')
}


try:
    print("Connecting to MariaDB...")
    conn = mariadb.connect(**db_config)
    print("Connection successful!")

    cursor = conn.cursor()

except Exception as e:
    print("Something goes wrong with the database .", e)

def readShot(shooter: int):
    print("\nSelecting data...")
    select_query = "SELECT shooter_number, x, y FROM shots WHERE shooter_number LIKE ?"

    cursor.execute(select_query, (f"%{shooter}%")) # <--error : mariadb.ProgrammingError: Data argument must be Tuple or List

    print("Fetched data:")
    for row in cursor:
        print(f"shooter_number: {row[0]}, x: {row[1]}, y: {row[2]}")
