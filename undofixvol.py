import os

def undo_modifications(root_directory):
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file.endswith('screens.pup.bak'):
                full_path_bak = os.path.join(root, file)
                full_path_original = os.path.join(root, file.replace('.bak', ''))
                
                # Delete the modified screens.pup file
                if os.path.exists(full_path_original):
                    os.remove(full_path_original)
                
                # Rename screens.pup.bak back to screens.pup
                os.rename(full_path_bak, full_path_original)

# Specify your root directory here
root_directory = '.\\'
undo_modifications(root_directory)

print('Undo modifications completed.')
