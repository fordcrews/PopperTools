import os
import time
import zipfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class IniFileHandler(FileSystemEventHandler):
    def __init__(self, download_dir):
        self.download_dir = download_dir

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith(".ini"):
            ini_file_name = os.path.basename(file_path)
            base_name = os.path.splitext(ini_file_name)[0]
            new_ini_name = base_name + "_LW.ini"
            new_ini_path = os.path.join(self.download_dir, new_ini_name)

            # Retry mechanism to ensure the ini file is not being used
            if not self.rename_file_with_retries(file_path, new_ini_path):
                print(f"Error: Could not rename {file_path}")
                return

            # Find the most recent zip file
            zip_files = [f for f in os.listdir(self.download_dir) if f.endswith(".zip")]
            if not zip_files:
                return
            
            zip_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            most_recent_zip = zip_files[0]
            most_recent_zip_path = os.path.join(self.download_dir, most_recent_zip)

            if self.is_file_complete(most_recent_zip_path):
                self.process_zip_file(most_recent_zip_path, new_ini_path, base_name + "_LW")

    def rename_file_with_retries(self, old_path, new_path, retries=10, delay=2):
        for _ in range(retries):
            try:
                os.rename(old_path, new_path)
                return True
            except PermissionError:
                time.sleep(delay)
        return False

    def is_file_complete(self, file_path):
        initial_size = os.path.getsize(file_path)
        time.sleep(2)  # Wait for 2 seconds
        return os.path.getsize(file_path) == initial_size

    def process_zip_file(self, zip_path, ini_file_path, new_base_name):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                vpx_files = [f for f in zip_ref.namelist() if f.endswith(".vpx")]

                if vpx_files:
                    # Extract the .vpx file
                    vpx_content = zip_ref.read(vpx_files[0])
                    vpx_file_name = new_base_name + ".vpx"

                    # Create new zip file
                    new_zip_path = os.path.join(self.download_dir, new_base_name + ".zip")
                    with zipfile.ZipFile(new_zip_path, 'w') as zip_write:
                        zip_write.writestr(vpx_file_name, vpx_content)
                        zip_write.write(ini_file_path, os.path.basename(ini_file_path))

                    print(f"Processed {new_zip_path}")

            # Retry mechanism to ensure the zip file is not being used
            if not self.remove_file_with_retries(zip_path):
                print(f"Error: Could not delete {zip_path}")

        except zipfile.BadZipFile as e:
            print(f"Error processing zip file {zip_path}: {e}")

    def remove_file_with_retries(self, file_path, retries=10, delay=2):
        for _ in range(retries):
            try:
                os.remove(file_path)
                return True
            except PermissionError:
                time.sleep(delay)
        return False

def monitor_download_folder(download_dir):
    event_handler = IniFileHandler(download_dir)
    observer = Observer()
    observer.schedule(event_handler, download_dir, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    download_directory = r"W:\Mega\LW Tables"
    monitor_download_folder(download_directory)
