import os
import re
import sqlite3
import difflib
import shutil
import argparse

# Function to fetch table names from the SQLite database
def fetch_table_names(database_path, debug=False):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(emulators);")
    emulator_columns = [column[1] for column in cursor.fetchall()]
    if debug:
        print(f"Columns in emulators table: {emulator_columns}")

    id_column = 'EMUID' if 'EMUID' in emulator_columns else emulator_columns[0]
    name_column = 'EmuName' if 'EmuName' in emulator_columns else emulator_columns[1]

    cursor.execute(f"SELECT {id_column} FROM emulators WHERE {name_column} LIKE '%Visual Pinball%'")
    visual_pinball_ids = [row[0] for row in cursor.fetchall()]

    if not visual_pinball_ids:
        print("No Visual Pinball emulators found.")
        conn.close()
        return []

    cursor.execute("PRAGMA table_info(Games);")
    game_columns = [column[1] for column in cursor.fetchall()]
    if debug:
        print(f"Columns in Games table: {game_columns}")

    game_display_column = 'GameDisplay' if 'GameDisplay' in game_columns else game_columns[0]
    emulator_id_column = 'EMUID' if 'EMUID' in game_columns else game_columns[1]

    placeholder = ', '.join(['?'] * len(visual_pinball_ids))
    cursor.execute(f"SELECT {game_display_column} FROM Games WHERE {emulator_id_column} IN ({placeholder})", visual_pinball_ids)
    table_names = [row[0] for row in cursor.fetchall()]

    if debug:
        print(f"Visual Pinball table names: {table_names}")

    conn.close()
    return table_names

# Function to clean and standardize filenames by removing common extraneous details
def clean_filename(filename):
    cleaned_filename = re.sub(r'[\[\(].*?[\]\)]', '', filename)
    cleaned_filename = re.sub(r'v\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'[-_]', ' ', cleaned_filename)
    return cleaned_filename.strip()

# Function to find the best match with similarity score
def find_best_match(filename, table_names, threshold=0.90, debug=False):
    cleaned_filename = clean_filename(filename)
    matches = []
    for table_name in table_names:
        cleaned_table_name = clean_filename(table_name)
        similarity = difflib.SequenceMatcher(None, cleaned_filename, cleaned_table_name).ratio()
        if similarity >= 0.80 and debug:
            print(f"Comparing '{cleaned_filename}' with '{cleaned_table_name}' - Similarity: {similarity:.2f}")
        if similarity >= threshold:
            matches.append((similarity, table_name))
    matches.sort(reverse=True, key=lambda x: x[0])
    return matches

# Function to process media files
def process_media_files(media_dir, table_names, media_types, backup_dir, dry_run=False, process_first=None, threshold=0.90, debug=False):
    summary = {
        "Audio": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "AudioLaunch": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "BackGlass": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "DMD": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "GameHelp": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "GameInfo": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "GameSelect": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Loading": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Menu": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "mscomctl.ocx": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Other1": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Other2": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "PlayField": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "System": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Topper": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
        "Wheel": {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0},
    }
    total_summary = {"Processed": 0, "Linked": 0, "Renamed": 0, "BackedUp": 0, "Left": 0}

    table_names_to_process = table_names[:process_first] if process_first else table_names

    for root, _, files in os.walk(media_dir):
        if debug:
            print(f"\nProcessing directory: {root}")
            print(f"Number of files: {len(files)}")

        for file in files:
            if any(file.endswith(ext) for ext in media_types):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                matches = find_best_match(file_name, table_names_to_process, threshold, debug=debug)
                media_type = next((key for key in summary if key in root), "Other")

                summary[media_type]["Processed"] += 1
                total_summary["Processed"] += 1

                if matches:
                    best_match = matches[0][1]
                    confidence = matches[0][0] * 100
                    new_file_path = os.path.join(root, best_match + os.path.splitext(file)[1])
                    if confidence >= 95:
                        if new_file_path != file_path:
                            if dry_run:
                                print(f"{confidence:.2f}% - Dry run: Would rename: {file_path} -> {new_file_path}")
                                summary[media_type]["Renamed"] += 1
                                total_summary["Renamed"] += 1
                            else:
                                if not os.path.exists(new_file_path):
                                    os.rename(file_path, new_file_path)
                                    print(f"{confidence:.2f}% - Renamed: {file_path} -> {new_file_path}")
                                    summary[media_type]["Renamed"] += 1
                                    total_summary["Renamed"] += 1
                                else:
                                    print(f"{confidence:.2f}% - Skipped renaming {file_path} because {new_file_path} already exists")
                                    summary[media_type]["Left"] += 1
                                    total_summary["Left"] += 1
                        else:
                            summary[media_type]["Left"] += 1
                            total_summary["Left"] += 1
                    else:
                        if dry_run:
                            print(f"Dry run: Would move: {file_path} -> {backup_dir}")
                            summary[media_type]["BackedUp"] += 1
                            total_summary["BackedUp"] += 1
                        else:
                            os.makedirs(backup_dir, exist_ok=True)
                            shutil.move(file_path, backup_dir)
                            print(f"Moved: {file_path} -> {backup_dir}")
                            summary[media_type]["BackedUp"] += 1
                            total_summary["BackedUp"] += 1
                else:
                    if dry_run:
                        print(f"Dry run: Would move: {file_path} -> {backup_dir}")
                        summary[media_type]["BackedUp"] += 1
                        total_summary["BackedUp"] += 1
                    else:
                        os.makedirs(backup_dir, exist_ok=True)
                        shutil.move(file_path, backup_dir)
                        print(f"Moved: {file_path} -> {backup_dir}")
                        summary[media_type]["BackedUp"] += 1
                        total_summary["BackedUp"] += 1

    print("\nSummary:")
    for key, value in summary.items():
        print(f"{key}: Processed: {value['Processed']}, Renamed: {value['Renamed']}, BackedUp: {value['BackedUp']}, Left: {value['Left']}")
    print(f"\nTotal: Processed: {total_summary['Processed']}, Renamed: {total_summary['Renamed']}, BackedUp: {total_summary['BackedUp']}, Left: {total_summary['Left']}")

def main():
    parser = argparse.ArgumentParser(description='Rename or move media files based on matching table names.')
    parser.add_argument('--dry-run', action='store_true', help='Show what actions would be taken without making changes')
    parser.add_argument('--process-first', type=int, help='Process only the first x tables')
    parser.add_argument('--debug', action='store_true', help='Show detailed debug information for matches 80% or better')
    args = parser.parse_args()

    database_path = r"C:\vPinball\PinUPSystem\PUPDatabase.db"
    media_dir = r"C:\vPinball\PinUPSystem\POPMedia\Visual Pinball X"
    backup_dir = r"C:\vPinball\backupmedia\PinUPSystem\POPMedia\Visual Pinball X"
    media_types = ['.jpg', '.mp4', '.png', '.apng', '.mp3']

    table_names = fetch_table_names(database_path, debug=args.debug)
    process_media_files(media_dir, table_names, media_types, backup_dir, dry_run=args.dry_run, process_first=args.process_first, debug=args.debug)

if __name__ == "__main__":
    main()
