import requests
import pandas as pd
import sqlite3
from io import StringIO

# Configuration
spreadsheet_id = "1trrUwxqfNkuzuHGPR8kzvETQa6BeZHHQnH1yLcd9UlM"
sheets = [
    ("0", "Pinup14"),          
    ("1670768223", "Emulators"),  
    ("819668133", "Manufactures"),   
    ("481765208", "Table Authors"),
    ("243589231", "PupSystems"), 	
    ("734003010", "Features"),
    ("349917615", "Themes"),
    ("242867294", "Other")
]
download_dir = "."

# Create a new SQLite database (or connect to an existing one)
conn = sqlite3.connect('google_spreadsheet.db')
cursor = conn.cursor()

# Fetch and save each sheet
for gid, table_name in sheets:
    # Fetch the CSV content for the current sheet
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(spreadsheet_url)
    response.raise_for_status()  # Ensure we notice bad responses

    # Load the CSV content into a DataFrame
    csv_content = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_content))

    # Save each sheet to a separate table in the SQLite database
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"Sheet with gid {gid} has been saved to table {table_name} in the SQLite database.")

# Commit changes and close the connection
conn.commit()
conn.close()

print("All sheets have been saved to the SQLite database.")
