import os
import re
import sqlite3
import difflib
import argparse

# Function to fetch table names from the SQLite database
def fetch_table_names(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # List columns in the emulators table
    cursor.execute("PRAGMA table_info(emulators);")
    emulator_columns = [column[1] for column in cursor.fetchall()]
    print(f"Columns in emulators table: {emulator_columns}")

    # Adjust column names if necessary
    id_column = 'EMUID' if 'EMUID' in emulator_columns else emulator_columns[0]
    name_column = 'EmuName' if 'EmuName' in emulator_columns else emulator_columns[1]

    # Fetch Visual Pinball emulator IDs
    cursor.execute(f"SELECT {id_column} FROM emulators WHERE {name_column} LIKE '%Visual Pinball%'")
    visual_pinball_ids = [row[0] for row in cursor.fetchall()]

    if not visual_pinball_ids:
        print("No Visual Pinball emulators found.")
        conn.close()
        return []

    print(f"Visual Pinball Emulator IDs: {visual_pinball_ids}")

    # List columns in the games table
    cursor.execute("PRAGMA table_info(Games);")
    game_columns = [column[1] for column in cursor.fetchall()]
    print(f"Columns in Games table: {game_columns}")

    game_display_column = 'GameDisplay' if 'GameDisplay' in game_columns else game_columns[0]
    emulator_id_column = 'EMUID' if 'EMUID' in game_columns else game_columns[1]

    # Fetch table names for Visual Pinball emulators
    placeholder = ', '.join(['?'] * len(visual_pinball_ids))
    cursor.execute(f"SELECT {game_display_column} FROM Games WHERE {emulator_id_column} IN ({placeholder})", visual_pinball_ids)
    table_names = [row[0] for row in cursor.fetchall()]

    if not table_names:
        print("No tables found for Visual Pinball emulators.")
    
    print(f"Found {len(table_names)} Visual Pinball tables.")
    conn.close()
    return table_names

# Function to clean and standardize filenames by removing common extraneous details
def clean_filename(filename):
    # Remove version numbers, resolution indicators, and other common extraneous details
    cleaned_filename = re.sub(r'[\[\(].*?[\]\)]', '', filename)
    cleaned_filename = re.sub(r'v\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'[-_]', ' ', cleaned_filename)
    return cleaned_filename.strip()

# Function to find the best match with similarity score
def find_best_match(filename, table_names, threshold=0.90):
    cleaned_filename = clean_filename(filename)
    matches = []
    for table_name in table_names:
        cleaned_table_name = clean_filename(table_name)
        similarity = difflib.SequenceMatcher(None, cleaned_filename, cleaned_table_name).ratio()
        if similarity >= threshold:
            matches.append((similarity, table_name))
    matches.sort(reverse=True, key=lambda x: x[0])
    return matches

# Function to create hard links
def create_hard_links(media_dir, table_names, media_types, dry_run=False, process_first=None, threshold=0.90):
    matches_list = []

    for root, _, files in os.walk(media_dir):
        processed_count = 0
        for file in files:
            if any(file.endswith(ext) for ext in media_types):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                matches = find_best_match(file_name, table_names, threshold)
                if matches:
                    best_match = matches[0][1]
                    confidence = matches[0][0] * 100
                    link_name = os.path.join(root, best_match + os.path.splitext(file)[1])
                    matches_list.append((confidence, link_name, file_path, file_name, best_match))
                processed_count += 1
        print(f"Processed {processed_count} files in directory: {root}")

    # Sort matches by confidence
    matches_list.sort(reverse=True, key=lambda x: x[0])

    # Process matches
    for idx, (confidence, link_name, file_path, file_name, best_match) in enumerate(matches_list):
        if process_first is not None and idx >= process_first:
            break
        if dry_run:
            print(f"{idx + 1}. {confidence:.2f}% - Dry run: Would create link: {link_name} -> {file_path}")
        else:
            if not os.path.exists(link_name):
                if os.path.exists(file_path):
                    os.link(file_path, link_name)  # Create hard link
                    print(f"{idx + 1}. {confidence:.2f}% - Created hard link: {link_name} -> {file_path}")
                else:
                    print(f"Error: File {file_path} does not exist")

# Main function
def main():
    parser = argparse.ArgumentParser(description='Create hard links for media files matching table names.')
    parser.add_argument('--dry-run', action='store_true', help='Show what actions would be taken without making changes')
    parser.add_argument('--process-first', type=int, help='Process only the first x items with highest confidence matches')
    args = parser.parse_args()

    database_path = r"C:\vPinball\PinUPSystem\PUPDatabase.db"
    media_dir = r"C:\vPinball\PinUPSystem\POPMedia\Visual Pinball X"  # Only look at this directory for now
    media_types = ['.jpg', '.mp4', '.png', '.apng']

    table_names = fetch_table_names(database_path)
    create_hard_links(media_dir, table_names, media_types, dry_run=args.dry_run, process_first=args.process_first)

if __name__ == "__main__":
    main()
