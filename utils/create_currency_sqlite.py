import pandas as pd
import sqlite3

# Load the Excel file
file_path = '/Users/admin/code/backup_pa_tool/storage/Game_Currency_Server_List.xlsx'  # Replace with your file path
sheet1 = pd.read_excel(file_path, sheet_name=0)  # Server-Faction table

# Display the first few rows of the result
print(sheet1.head())

# Optionally, save to a new Excel file
sheet1.to_excel('/Users/admin/code/backup_pa_tool/storage/joined_output.xlsx', index=False)

# Save the result to a SQLite database
conn = sqlite3.connect('/Users/admin/code/backup_pa_tool/storage/joined_data2.db')
sheet1.to_sql('joined_table', conn, if_exists='replace', index=False)
conn.close()

print("Data has been saved to both Excel and SQLite.")