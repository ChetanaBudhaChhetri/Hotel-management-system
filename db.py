import sqlite3
from sqlite3 import Error
from config import Config


def get_connection():
    return sqlite3.connect(Config.DB_PATH)


def fetch_all(query, params=None):
    connection = get_connection()
    connection.row_factory = sqlite3.Row  # Enable column access by name
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [dict(row) for row in rows]  # Convert to dict


def fetch_one(query, params=None):
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    row = cursor.fetchone()
    cursor.close()
    connection.close()
    return dict(row) if row else None


def execute_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    connection.commit()
    cursor.close()
    connection.close()
