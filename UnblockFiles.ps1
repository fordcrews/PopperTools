# Define the directory path
$directoryPath = ".\"

# Get all files in the directory and subdirectories
$files = Get-ChildItem -Path $directoryPath -Recurse -File

# Unblock each file
foreach ($file in $files) {
    try {
        Unblock-File -Path $file.FullName
        Write-Host "Unblocked: $($file.FullName)"
    } catch {
        Write-Host "Failed to unblock: $($file.FullName) - $($_.Exception.Message)"
    }
}

Write-Host "All accessible files in $directoryPath have been processed."
