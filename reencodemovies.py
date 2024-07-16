import os
import subprocess
import shutil
import datetime
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ])

# Specify the full path to the FFmpeg executable
ffmpeg_path = r'C:\vPinball\PinUPSystem\Recordings\ffmpeg.exe'

def normalize_audio(directory):
    last_run_file = os.path.join(directory, 'last_run.txt')
    last_run_date = datetime.datetime.min

    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as file:
            last_run_date = datetime.datetime.fromisoformat(file.read().strip())

    def process_directory(current_directory):
        logging.debug(f"Checking directory: {current_directory}")
        for entry in os.listdir(current_directory):
            path = os.path.join(current_directory, entry)
            if os.path.isdir(path):
                if entry != 'original':
                    process_directory(path)
            elif path.endswith(('.mp4', '.mkv')):
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                if file_mtime > last_run_date:
                    logging.debug(f"Processing file: {entry}")
                    process_file(path, current_directory, 'normalize')
                else:
                    logging.debug(f"Skipping file: {entry}, not modified since last run.")

    def process_file(full_path, current_directory, mode):
        original_dir = os.path.join(current_directory, 'original')
        if not os.path.exists(original_dir):
            os.makedirs(original_dir)

        file = os.path.basename(full_path)
        backup_file = os.path.join(original_dir, file)
        normalized_file = os.path.join(current_directory, f'normalized_{file}')
        
        shutil.move(full_path, backup_file)

        # Check the original codec and resolution
        command = [
            ffmpeg_path,
            '-i', backup_file,
            '-hide_banner'
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = result.stderr.split('\n')

        original_codec = None
        original_resolution = None
        for line in lines:
            if 'Stream #0:0' in line and 'Video' in line:
                original_codec = line.split()[3]
                if 'x' in line:
                    resolution_part = line.split()[5]
                    width, height = map(int, resolution_part.split('x'))
                    original_resolution = (width, height)

        if mode == 'normalize':
            if original_codec == 'hevc':
                # Only normalize audio
                command = [
                    ffmpeg_path,
                    '-hwaccel', 'cuda',
                    '-i', backup_file,
                    '-c:v', 'copy',
                    '-af', 'loudnorm=I=-23:LRA=7:TP=-2',
                    '-ar', '44100',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-c:s', 'copy',  # Copy subtitle streams
                    normalized_file
                ]
            else:
                # Re-encode video to H.265 and normalize audio
                command = [
                    ffmpeg_path,
                    '-hwaccel', 'cuda',
                    '-i', backup_file,
                    '-c:v', 'hevc_nvenc',
                    '-b:v', '2M',  # Lower target average bitrate
                    '-maxrate', '4M',  # Lower maximum bitrate
                    '-bufsize', '4M',  # Buffer size
                    '-preset', 'slow',  # Slower preset for better compression
                    '-af', 'loudnorm=I=-23:LRA=7:TP=-2',
                    '-ar', '44100',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-c:s', 'copy',  # Copy subtitle streams
                    normalized_file
                ]
        elif mode == 'processtv':
            # Resize to 1080p if larger and re-encode with lower quality
            scale_filter = ''
            if original_resolution and (original_resolution[0] > 1920 or original_resolution[1] > 1080):
                scale_filter = '-vf scale=1920:1080'

            command = [
                ffmpeg_path,
                '-hwaccel', 'cuda',
                '-i', backup_file,
                '-c:v', 'hevc_nvenc',
                '-b:v', '1M',  # Lower target average bitrate for old TV shows
                '-maxrate', '2M',  # Lower maximum bitrate
                '-bufsize', '2M',  # Buffer size
                '-preset', 'slow',  # Slower preset for better compression
                '-af', 'loudnorm=I=-23:LRA=7:TP=-2',
                '-ar', '44100',
                '-c:a', 'aac',
                '-b:a', '96k',  # Lower audio bitrate for old TV shows
                '-c:s', 'copy',  # Copy subtitle streams
                scale_filter,
                normalized_file
            ]

        try:
            subprocess.run(command, check=True)
            os.rename(normalized_file, full_path)
            logging.debug(f"Completed processing on {file}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error processing file {file}: {e}")

    if sys.argv[1] == 'process':
        process_directory(directory)
        with open(last_run_file, 'w') as file:
            file.write(datetime.datetime.now().isoformat())
        logging.debug("Updated last run time.")

    elif sys.argv[1] == 'processtv':
        process_directory(directory)
        with open(last_run_file, 'w') as file:
            file.write(datetime.datetime.now().isoformat())
        logging.debug("Updated last run time.")

    elif sys.argv[1] == 'undo':
        undo_changes(directory)
        if os.path.exists(last_run_file):
            os.remove(last_run_file)
            logging.debug("Removed last run tracking file.")

    elif sys.argv[1] == 'finalize':
        finalize_changes(directory)

    else:
        logging.error("Invalid command. Usage: recursive_normalize.py [process|processtv|undo|finalize]")

def undo_changes(current_directory):
    original_dir = os.path.join(current_directory, 'original')
    if os.path.exists(original_dir):
        for file in os.listdir(original_dir):
            original_file_path = os.path.join(original_dir, file)
            target_file_path = os.path.join(current_directory, file)

            if os.path.exists(target_file_path):
                logging.debug(f"Removing normalized file: {target_file_path}")
                os.remove(target_file_path)

            shutil.move(original_file_path, current_directory)
            logging.debug(f"Restored original file: {file}")

        if not os.listdir(original_dir):
            os.rmdir(original_dir)
            logging.debug(f"Removed empty original directory: {original_dir}")

    for entry in os.listdir(current_directory):
        path = os.path.join(current_directory, entry)
        if os.path.isdir(path) and entry != 'original':
            undo_changes(path)

def finalize_changes(current_directory):
    original_dir = os.path.join(current_directory, 'original')
    if os.path.exists(original_dir):
        shutil.rmtree(original_dir)
        logging.debug(f"Removed original files directory: {original_dir}")
    for entry in os.listdir(current_directory):
        path = os.path.join(current_directory, entry)
        if os.path.isdir(path) and entry != 'original':
            finalize_changes(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: recursive_normalize.py [process|processtv|undo|finalize]")
    else:
        normalize_audio('.')
