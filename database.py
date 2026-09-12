import sqlite3

DATABASE = "lostlink.db"


def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_db_connection()

    # Create table if it does not exist
    connection.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            report_type TEXT NOT NULL,
            date_reported TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            image TEXT,
            contact TEXT
        )
    """)


    # Check existing columns
    columns = connection.execute(
        "PRAGMA table_info(items)"
    ).fetchall()


    column_names = [
        column["name"]
        for column in columns
    ]


    # Add image column if missing
    if "image" not in column_names:

        connection.execute("""
            ALTER TABLE items
            ADD COLUMN image TEXT
        """)


    # Add contact column if missing
    if "contact" not in column_names:

        connection.execute("""
            ALTER TABLE items
            ADD COLUMN contact TEXT
        """)


    connection.commit()

    connection.close()