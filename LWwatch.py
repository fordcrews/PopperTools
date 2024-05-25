import os
import time
import zipfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DownloadHandler(FileSystemEventHandler):
    def __init__(self, download_dir):
        self.download_dir = download_dir

    def on_modified(self, event):
        for filename in os.listdir(self.download_dir):
            if filename.endswith(".zip"):
                zip_path = os.path.join(self.download_dir, filename)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    vpx_files = [f for f in zip_ref.namelist() if f.endswith(".vpx")]

                    if vpx_files:
                        ini_files = [f for f in os.listdir(self.download_dir) if f.endswith(".ini")]
                        for ini_file in ini_files:
                            ini_file_path = os.path.join(self.download_dir, ini_file)
                            new_name = os.path.splitext(ini_file)[0]

                            # Rename zip file
                            new_zip_path = os.path.join(self.download_dir, new_name + ".zip")
                            os.rename(zip_path, new_zip_path)

                            # Rename .vpx file inside the zip
                            with zipfile.ZipFile(new_zip_path, 'r') as zip_read:
                                zip_contents = zip_read.namelist()
                                with zipfile.ZipFile(new_zip_path + ".tmp", 'w') as zip_write:
                                    for item in zip_contents:
                                        if item.endswith(".vpx"):
                                            vpx_content = zip_read.read(item)
                                            zip_write.writestr(new_name + ".vpx", vpx_content)
                                        else:
                                            zip_write.writestr(item, zip_read.read(item))
                                    # Add .ini file to the zip
                                    zip_write.write(ini_file_path, os.path.basename(ini_file_path))
                            
                            os.remove(new_zip_path)
                            os.rename(new_zip_path + ".tmp", new_zip_path)
                            print(f"Processed {new_zip_path}")


def monitor_download_folder(download_dir):
    event_handler = DownloadHandler(download_dir)
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
