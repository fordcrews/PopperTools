# Define the directory path
$directoryPath = ".\"

# Get all files in the directory and subdirectories
$files = Get-ChildItem -Path $directoryPath -Recurse

# Unblock each file
foreach ($file in $files) {
    Unblock-File -Path $file.FullName
}

Write-Host "All files in $directoryPath have been unblocked."
