import sqlite3
import os
import zipfile
import sys
from fnmatch import fnmatch

# Configuration
backup_folder = "C:\\vpinball\\Backups"
db_path = "C:\\vPinball\\PinUPSystem\\PupDatabase.db"
additional_dirs = ["C:\\vpinball\\PinUPSystem\\PUPVideos", "C:\\vpinball\\PinUPSystem\\POPMedia"]
emulators = ["Future Pinball", "Visual Pinball X"]
debug = len(sys.argv) > 1 and sys.argv[1].lower() == 'debug'

# Ensure the backup folder exists
os.makedirs(backup_folder, exist_ok=True)

def connect_db(db_path):
    return sqlite3.connect(db_path)

def fetch_games_data(conn):
    cursor = conn.cursor()
    try:
        query = """
        SELECT games.GameFileName, games.ROM, emulators.emuname, emulators.DirGames
        FROM games
        JOIN emulators ON games.emuid = emulators.emuid
        WHERE emulators.emuname IN (?, ?)
        """
        cursor.execute(query, ('Future Pinball', 'Visual Pinball X'))
    except sqlite3.OperationalError as e:
        if debug: print(f"Error: {e}")
        return []
    return cursor.fetchall()

def backup_files(files, backup_zip, root_directories):
    for file in files:
        if os.path.exists(file):
            arcname = os.path.relpath(file, start=os.path.commonpath(root_directories + additional_dirs))
            if debug: print(f"Adding {file} as {arcname} to zip")
            backup_zip.write(file, arcname)
        else:
            if debug: print(f"File does not exist: {file}")

def get_files_to_backup(game_file, rom_file, dir_games):
    files_to_backup = []

    base_game_file = os.path.splitext(game_file)[0]

    relevant_directories = [dir_games] + additional_dirs

    # Search in the main directories
    for directory in relevant_directories:
        if debug: print(f"Searching in directory: {directory}")
        for root, _, files in os.walk(directory):
            for file in files:
                # Match both the base game file and any SCREEN3 videos
                if fnmatch(file, f"{base_game_file}.*") or (rom_file and fnmatch(file, f"{rom_file}.*")) or fnmatch(file, f"*SCREEN3*"):
                    file_path = os.path.join(root, file)
                    if debug: print(f"Found file to backup: {file_path}")
                    files_to_backup.append(file_path)

    # Specific search for Future Pinball cfg files
    if os.path.splitext(game_file)[1] == '.fpt':
        cfg_directory = "C:\\vpinball\\FuturePinball"
        if debug: print(f"Searching for cfg files in directory: {cfg_directory}")
        for root, _, files in os.walk(cfg_directory):
            for file in files:
                if fnmatch(file, f"{base_game_file}.cfg"):
                    file_path = os.path.join(root, file)
                    if debug: print(f"Found Future Pinball cfg file to backup: {file_path}")
                    files_to_backup.append(file_path)

    # Search for PUPVideo files in specific ROM directory
    if rom_file:
        pupvideos_directory = os.path.join("C:\\vpinball\\PinUPSystem\\PUPVideos", rom_file)
        if os.path.isdir(pupvideos_directory):
            if debug: print(f"Searching for video files in directory: {pupvideos_directory}")
            for root, _, files in os.walk(pupvideos_directory):
                for file in files:
                    # Match both the base rom file and any SCREEN3 videos
                    if fnmatch(file, f"{base_game_file}.*") or fnmatch(file, f"*SCREEN3*"):
                        file_path = os.path.join(root, file)
                        if debug: print(f"Found video file to backup: {file_path}")
                        files_to_backup.append(file_path)

    return files_to_backup, relevant_directories


def main():
    conn = connect_db(db_path)
    games_data = fetch_games_data(conn)
    conn.close()

    for game_file, rom_file, emuname, dir_games in games_data:
        if not game_file and not rom_file:
            continue

        if os.path.splitext(game_file)[1] == '.vpx' and emuname != 'Visual Pinball X':
            continue
        if os.path.splitext(game_file)[1] == '.fpt' and emuname != 'Future Pinball':
            continue

        if debug:
            print(f"Processing game: {game_file}, rom: {rom_file}, emulator: {emuname}, directory: {dir_games}")
        
        files_to_backup, relevant_directories = get_files_to_backup(game_file, rom_file, dir_games)
        
        if not files_to_backup:
            if debug: print(f"No files found for game: {game_file} and rom: {rom_file}")
            continue

        # Create directory structure for the backup file
        game_file_name = os.path.splitext(os.path.basename(game_file))[0]
        backup_zip_path = os.path.join(backup_folder, f"{game_file_name}_backup.zip")
        os.makedirs(os.path.dirname(backup_zip_path), exist_ok=True)
        
        if debug: print(f"Creating backup zip at: {backup_zip_path}")
        with zipfile.ZipFile(backup_zip_path, 'w') as backup_zip:
            backup_files(files_to_backup, backup_zip, relevant_directories)
        if debug: print(f"Backup for {game_file_name} completed")

if __name__ == "__main__":
    main()
