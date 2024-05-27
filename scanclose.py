import os
import re
import sqlite3
import difflib
import shutil
import argparse
import html

# Function to fetch table filenames from the SQLite database
def fetch_table_filenames(database_path, debug=False):
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

    game_filename_column = 'GameFileName' if 'GameFileName' in game_columns else game_columns[0]
    emulator_id_column = 'EMUID' if 'EMUID' in game_columns else game_columns[1]

    placeholder = ', '.join(['?'] * len(visual_pinball_ids))
    cursor.execute(f"SELECT {game_filename_column} FROM Games WHERE {emulator_id_column} IN ({placeholder}) ORDER BY {game_filename_column}", visual_pinball_ids)
    table_filenames = [os.path.splitext(row[0])[0] for row in cursor.fetchall()]

    if debug:
        print(f"Visual Pinball table filenames: {table_filenames}")

    conn.close()
    return table_filenames

# Function to clean and standardize filenames by removing common extraneous details
def clean_filename(filename):
    cleaned_filename = re.sub(r'[\[\(].*?[\]\)]', '', filename)
    cleaned_filename = re.sub(r'v\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'\d+\.\d+', '', cleaned_filename)
    cleaned_filename = re.sub(r'[-_]', ' ', cleaned_filename)
    return cleaned_filename.strip()

# Function to find the best match with similarity score
def find_best_matches(filename, table_filenames, threshold=0.90, debug=False):
    cleaned_filename = clean_filename(filename)
    matches = []
    for table_filename in table_filenames:
        cleaned_table_filename = clean_filename(table_filename)
        similarity = difflib.SequenceMatcher(None, cleaned_filename, cleaned_table_filename).ratio()
        if similarity >= 0.80 and debug:
            print(f"Comparing '{cleaned_filename}' with '{cleaned_table_filename}' - Similarity: {similarity:.2f}")
        if similarity >= threshold:
            matches.append((similarity, table_filename))
    matches.sort(reverse=True, key=lambda x: x[0])
    return matches

# Function to ensure unique filenames in the backup directory
def ensure_unique_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1
    return unique_filename

# Function to process media files
def process_media_files(media_dir, table_filenames, media_types, backup_dir, dry_run=False, threshold=0.90, debug=False):
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

    actions = []

    for root, _, files in sorted(os.walk(media_dir), key=lambda x: x[0]):
        if debug:
            print(f"\nProcessing directory: {root}")
            print(f"Number of files: {len(files)}")

        for file in sorted(files):
            if any(file.endswith(ext) for ext in media_types):
                file_path = os.path.join(root, file)
                original_file_path = file_path  # Track the original file path
                file_name = os.path.splitext(file)[0]
                matches = find_best_matches(file_name, table_filenames, threshold, debug=debug)
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
                                actions.append(["Rename", best_match, file_path, new_file_path, f"{confidence:.2f}%"])
                                summary[media_type]["Renamed"] += 1
                                total_summary["Renamed"] += 1
                            else:
                                if not os.path.exists(new_file_path):
                                    os.rename(file_path, new_file_path)
                                    actions.append(["Rename", best_match, file_path, new_file_path, f"{confidence:.2f}%"])
                                    summary[media_type]["Renamed"] += 1
                                    total_summary["Renamed"] += 1
                                    file_path = new_file_path  # Update file_path to the new path
                                else:
                                    summary[media_type]["Left"] += 1
                                    total_summary["Left"] += 1

                        for match in matches[1:]:
                            link_name = os.path.join(root, match[1] + os.path.splitext(file)[1])
                            if dry_run:
                                actions.append(["Link", match[1], original_file_path, link_name, f"{match[0]*100:.2f}%"])
                                summary[media_type]["Linked"] += 1
                                total_summary["Linked"] += 1
                            else:
                                if os.path.exists(original_file_path) and not os.path.exists(link_name):
                                    os.link(original_file_path, link_name)
                                    actions.append(["Link", match[1], original_file_path, link_name, f"{match[0]*100:.2f}%"])
                                    summary[media_type]["Linked"] += 1
                                    total_summary["Linked"] += 1
                    else:
                        backup_subdir = os.path.relpath(root, media_dir)
                        backup_path = os.path.join(backup_dir, backup_subdir)
                        if dry_run:
                            backup_filename = ensure_unique_filename(backup_path, os.path.basename(file_path))
                            actions.append(["Move", "", file_path, os.path.join(backup_path, backup_filename), f"{confidence:.2f}% (below threshold)"])
                            summary[media_type]["BackedUp"] += 1
                            total_summary["BackedUp"] += 1
                        else:
                            os.makedirs(backup_path, exist_ok=True)
                            backup_filename = ensure_unique_filename(backup_path, os.path.basename(file_path))
                            shutil.move(file_path, os.path.join(backup_path, backup_filename))
                            actions.append(["Move", "", file_path, os.path.join(backup_path, backup_filename), f"{confidence:.2f}% (below threshold)"])
                            summary[media_type]["BackedUp"] += 1
                            total_summary["BackedUp"] += 1
                else:
                    backup_subdir = os.path.relpath(root, media_dir)
                    backup_path = os.path.join(backup_dir, backup_subdir)
                    if dry_run:
                        backup_filename = ensure_unique_filename(backup_path, os.path.basename(file_path))
                        actions.append(["Move", "", file_path, os.path.join(backup_path, backup_filename), "No close matches found"])
                        summary[media_type]["BackedUp"] += 1
                        total_summary["BackedUp"] += 1
                    else:
                        os.makedirs(backup_path, exist_ok=True)
                        backup_filename = ensure_unique_filename(backup_path, os.path.basename(file_path))
                        shutil.move(file_path, os.path.join(backup_path, backup_filename))
                        actions.append(["Move", "", file_path, os.path.join(backup_path, backup_filename), "No close matches found"])
                        summary[media_type]["BackedUp"] += 1
                        total_summary["BackedUp"] += 1

    # Delete old report.html if it exists
    if os.path.exists("report.html"):
        os.remove("report.html")

    # Generate HTML report
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.min.css">
<link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap4.min.css">
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap4.min.js"></script>
<title>Media Processing Report</title>
</head>
<body>
<div class="container">
<h2>Media Processing Report</h2>
<table id="report" class="table table-striped table-bordered" style="width:100%">
<thead>
<tr>
<th>Action</th>
<th>Table Filename</th>
<th>Original File Name</th>
<th>Replacement File Name</th>
<th>% Match</th>
</tr>
</thead>
<tbody>
"""

    for action in actions:
        html_content += f"<tr><td>{html.escape(action[0])}</td><td>{html.escape(action[1])}</td><td>{html.escape(action[2])}</td><td>{html.escape(action[3])}</td><td>{html.escape(action[4])}</td></tr>"

    html_content += """
</tbody>
</table>
<script>
$(document).ready(function() {
$('#report').DataTable();
} );
</script>
</div>
</body>
</html>
"""

    with open("report.html", "w", encoding="utf-8") as report_file:
        report_file.write(html_content)

    print("\nSummary:")
    for key, value in summary.items():
        print(f"{key}: Processed: {value['Processed']}, Linked: {value['Linked']}, Renamed: {value['Renamed']}, BackedUp: {value['BackedUp']}, Left: {value['Left']}")
    print(f"\nTotal: Processed: {total_summary['Processed']}, Linked: {total_summary['Linked']}, Renamed: {total_summary['Renamed']}, BackedUp: {total_summary['BackedUp']}, Left: {total_summary['Left']}")

def main():
    parser = argparse.ArgumentParser(description='Rename or move media files based on matching table filenames.')
    parser.add_argument('--dry-run', action='store_true', help='Show what actions would be taken without making changes')
    parser.add_argument('--debug', action='store_true', help='Show detailed debug information for matches 80% or better')
    args = parser.parse_args()

    database_path = r"C:\vPinball\PinUPSystem\PUPDatabase.db"
    media_dir = r"C:\vPinball\PinUPSystem\POPMedia\Visual Pinball X"
    backup_dir = r"C:\vPinball\backupmedia\PinUPSystem\POPMedia\Visual Pinball X"
    media_types = ['.jpg', '.mp4', '.png', '.apng', '.mp3']

    table_filenames = fetch_table_filenames(database_path, debug=args.debug)
    process_media_files(media_dir, table_filenames, media_types, backup_dir, dry_run=args.dry_run, threshold=0.90, debug=args.debug)

if __name__ == "__main__":
    main()
