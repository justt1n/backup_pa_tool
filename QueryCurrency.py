import os
import sqlite3

import pandas as pd
from pydantic import BaseModel


class CurrencyQueryItem(BaseModel):
    ID: str
    Game: str
    Server: str
    Faction: str


def query_currency(db_path: str, game_id: str) -> CurrencyQueryItem:
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the query
    query = "SELECT * FROM game_data WHERE LOWER(ID) = LOWER(?)"

    # Execute the query
    cursor.execute(query, (game_id,))

    # Fetch the first result
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    return CurrencyQueryItem(ID=result[0], Game=result[1], Server=result[2], Faction=result[3])


def query_by_game(db_path: str, game_name: str):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the query
    query = "SELECT * FROM game_data WHERE LOWER(Game) LIKE LOWER(?)"

    # Execute the query
    cursor.execute(query, (f"%{game_name}%",))

    # Fetch all results
    results = cursor.fetchall()

    # Retrieve column names
    col_names = [description[0] for description in cursor.description]

    # Close the connection
    conn.close()

    return col_names, results


def export_to_excel(file_name: str, col_names: list, data: list):
    # Define the file path in /storage directory
    storage_path = 'storage/'
    file_path = os.path.join(storage_path, file_name)

    # Ensure the /storage directory exists
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)

    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"File '{file_path}' already exists. Please choose a different name or delete the existing file.")
        return

    # Convert data to a DataFrame
    df = pd.DataFrame(data, columns=col_names)

    # Write data to Excel
    df.to_excel(file_path, index=False)

    print(f"Data successfully exported to '{file_path}'.")


def main():
    db_path = 'storage/joined_data.db'

    while True:
        game_name = input("Enter game name to query (or type 'exit' to quit): ").strip()
        if game_name.lower() == 'exit':
            print("Exiting the program.")
            break

        col_names, results = query_by_game(db_path, game_name)

        if results:
            print("Results:")
            print(col_names)
            for row in results:
                print(row)

            export_choice = input("Do you want to export the results to an Excel file? (yes/no): ").strip().lower()
            if export_choice == 'yes':
                file_name = input("Enter the desired file name for the Excel file (e.g., 'output'): ").strip() + ".xlsx"
                export_to_excel(file_name, col_names, results)
        else:
            print(f"No results found for the game '{game_name}'.")


if __name__ == "__main__":
    main()
