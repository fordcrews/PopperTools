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

            # Find the most recent zip file
            zip_files = [f for f in os.listdir(self.download_dir) if f.endswith(".zip")]
            if not zip_files:
                return
            
            zip_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            most_recent_zip = zip_files[0]
            most_recent_zip_path = os.path.join(self.download_dir, most_recent_zip)

            with zipfile.ZipFile(most_recent_zip_path, 'r') as zip_ref:
                vpx_files = [f for f in zip_ref.namelist() if f.endswith(".vpx")]

                if vpx_files:
                    new_zip_path = os.path.join(self.download_dir, base_name + ".zip")

                    with zipfile.ZipFile(new_zip_path, 'w') as zip_write:
                        for item in zip_ref.infolist():
                            if item.filename.endswith(".vpx"):
                                vpx_content = zip_ref.read(item.filename)
                                zip_write.writestr(base_name + ".vpx", vpx_content)
                            else:
                                zip_write.writestr(item.filename, zip_ref.read(item.filename))
                        
                        # Add .ini file to the zip
                        zip_write.write(file_path, ini_file_name)
            
            os.remove(most_recent_zip_path)
            print(f"Processed {new_zip_path}")

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
    download_directory = "path_to_your_download_directory"
    monitor_download_folder(download_directory)
