import os
import csv
import shutil

def modify_screens_priority_with_backup_logging_and_conditions(root_directory, log_file_path):
    with open(log_file_path, 'w') as log_file:
        for root, dirs, files in os.walk(root_directory):
            triggers_path = os.path.join(root, 'triggers.pup')
            screens_path = os.path.join(root, 'screens.pup')
            backup_path = screens_path + '.bak'

            try:
                if os.path.exists(triggers_path) and os.path.exists(screens_path):
                    shutil.copyfile(screens_path, backup_path)

                    screen_nums_to_modify = []

                    with open(triggers_path, 'r', newline='') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            if 'ScreenNum' in row:
                                screen_nums_to_modify.append(row['ScreenNum'])

                    modified_lines = []
                    with open(screens_path, 'r', newline='') as file:
                        reader = csv.DictReader(file)
                        fieldnames = reader.fieldnames
                        if not fieldnames or 'ScreenNum' not in fieldnames or 'Priority' not in fieldnames or 'ScreenDes' not in fieldnames:
                            raise ValueError("Missing required fields in screens.pup")

                        for line in reader:
                            if line.get('ScreenNum') in screen_nums_to_modify:
                                line['Priority'] = '35'
                            # Check for "BackGlass" or "Music" in ScreenDes and set Priority to 60
                            if "backglass" in line.get('ScreenDes', '').lower() or "music" in line.get('ScreenDes', '').lower():
                                line['Priority'] = '30'
                            modified_lines.append(line)

                    with open(screens_path, 'w', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(modified_lines)
            except Exception as e:
                log_file.write(f"Error processing {screens_path}: {e}\n")

root_directory = '.\\'
log_file_path = '.\\log_file.txt'

modify_screens_priority_with_backup_logging_and_conditions(root_directory, log_file_path)

print('Priority modification process completed with additional conditions and logging.')
