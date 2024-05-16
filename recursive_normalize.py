import os
import subprocess
import shutil
import datetime
import sys

# Specify the full path to the FFmpeg executable
ffmpeg_path = r'C:\vPinball\PinUPSystem\Recordings\ffmpeg'

def normalize_audio(directory):
    last_run_file = os.path.join(directory, 'last_run.txt')
    last_run_date = datetime.datetime.min

    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as file:
            last_run_date = datetime.datetime.fromisoformat(file.read().strip())

    def process_directory(current_directory):
        print(f"Checking directory: {current_directory}")  # Debug: show current directory being processed
        for entry in os.listdir(current_directory):
            path = os.path.join(current_directory, entry)
            if os.path.isdir(path):
                if entry != 'original':
                    process_directory(path)
            elif path.endswith('.mp4'):
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                if file_mtime > last_run_date:
                    print(f"Processing file: {entry}")  # Debug: processing this file
                    process_file(path, current_directory)
                else:
                    print(f"Skipping file: {entry}, not modified since last run.")  # Debug: file skipped

    def process_file(full_path, current_directory):
        original_dir = os.path.join(current_directory, 'original')
        if not os.path.exists(original_dir):
            os.makedirs(original_dir)

        file = os.path.basename(full_path)
        backup_file = os.path.join(original_dir, file)
        normalized_file = os.path.join(current_directory, f'normalized_{file}')
        
        shutil.move(full_path, backup_file)
        command = [
            ffmpeg_path,
            '-i', backup_file,
            '-c:v', 'libx265', '-crf', '28', '-preset', 'fast',
            '-af', 'loudnorm=I=-23:LRA=7:TP=-2', '-ar', '44100', '-c:a', 'aac', '-b:a', '128k',
            normalized_file
        ]
        subprocess.run(command, check=True)
        os.rename(normalized_file, full_path)
        print(f"Completed processing on {file}")  # Debug: completed processing

    if sys.argv[1] == 'process':
        process_directory(directory)
        with open(last_run_file, 'w') as file:
            file.write(datetime.datetime.now().isoformat())
        print("Updated last run time.")

    elif sys.argv[1] == 'undo':
        undo_changes(directory)
        if os.path.exists(last_run_file):
            os.remove(last_run_file)
            print("Removed last run tracking file.")

    elif sys.argv[1] == 'finalize':
        finalize_changes(directory)

    else:
        print("Invalid command. Usage: recursive_normalize.py [process|undo|finalize]")

def undo_changes(current_directory):
    original_dir = os.path.join(current_directory, 'original')
    if os.path.exists(original_dir):
        for file in os.listdir(original_dir):
            original_file_path = os.path.join(original_dir, file)
            target_file_path = os.path.join(current_directory, file)

            # Check if the target file path exists and remove it to prevent conflicts
            if os.path.exists(target_file_path):
                print(f"Removing normalized file: {target_file_path}")  # Debug: Notify removal
                os.remove(target_file_path)

            # Move the original file back to the main directory
            shutil.move(original_file_path, current_directory)
            print(f"Restored original file: {file}")  # Debug: Notify restoration

        # Remove the now-empty 'original' directory
        if not os.listdir(original_dir):
            os.rmdir(original_dir)
            print(f"Removed empty original directory: {original_dir}")  # Debug: Notify directory removal

    for entry in os.listdir(current_directory):
        path = os.path.join(current_directory, entry)
        if os.path.isdir(path) and entry != 'original':
            undo_changes(path)

def finalize_changes(current_directory):
    original_dir = os.path.join(current_directory, 'original')
    if os.path.exists(original_dir):
        shutil.rmtree(original_dir)
        print(f"Removed original files directory: {original_dir}")  # Debug: Notify removal
    for entry in os.listdir(current_directory):
        path = os.path.join(current_directory, entry)
        if os.path.isdir(path) and entry != 'original':
            finalize_changes(path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: recursive_normalize.py [process|undo|finalize]")
    else:
        normalize_audio('.')
