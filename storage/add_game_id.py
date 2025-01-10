import sqlite3


def add_auto_increment_id(db_path, table_name):
    """
    Adds an auto-incrementing 'id' column to an existing SQLite table.

    :param db_path: Path to the SQLite database file.
    :param table_name: Name of the existing table to modify.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the existing table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Check if 'id' column already exists
        if 'id' in column_names:
            print(f"Table '{table_name}' already has an 'id' column.")
            return

        # Create a new table with an 'id' column added
        new_table_name = f"{table_name}_new"
        columns_definition = ", ".join([f"{col[1]} {col[2]}" for col in columns])
        create_table_sql = f"""
            CREATE TABLE {new_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columns_definition}
            )
        """
        cursor.execute(create_table_sql)

        # Copy data from the old table to the new table
        columns_without_types = ", ".join(column_names)
        cursor.execute(f"""
            INSERT INTO {new_table_name} ({columns_without_types})
            SELECT {columns_without_types} FROM {table_name}
        """)

        # Drop the old table and rename the new table
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

        conn.commit()
        print(f"Auto-incrementing 'id' column added to '{table_name}' successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        conn.close()


# Example usage
db_path = "joined_data.db"  # Path to your SQLite database file
table_name = "joined_data"  # Name of the table to modify

add_auto_increment_id(db_path, table_name)
