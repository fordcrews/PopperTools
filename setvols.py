import os
import csv

def modify_priority_conditionally(root_directory):
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file == 'screens.pup':
                full_path = os.path.join(root, file)
                backup_path = full_path + '.bak'
                
                # Copy the screens.pup to screens.bak
                os.system(f'copy "{full_path}" "{backup_path}"')
                
                # Read the original file
                with open(full_path, 'r', newline='') as original_file:
                    reader = csv.reader(original_file)
                    lines = list(reader)
                
                if lines:
                    header = lines[0]
                    priority_index = header.index('Priority') if 'Priority' in header else None
                    screendes_index = header.index('ScreenDes') if 'ScreenDes' in header else None
                    
                    if priority_index is not None and screendes_index is not None:
                        for line in lines[1:]:  # Skip the header line
                            if len(line) > max(priority_index, screendes_index):  # Check if the fields exist
                                if "music" in line[screendes_index].lower() or "video" in line[screendes_index].lower():
                                    line[priority_index] = '60'
                
                # Write the modified data back to screens.pup
                with open(full_path, 'w', newline='') as modified_file:
                    writer = csv.writer(modified_file)
                    writer.writerows(lines)

# Specify your root directory here
root_directory = '.\\'
modify_priority_conditionally(root_directory)

print('Conditional modification completed.')
