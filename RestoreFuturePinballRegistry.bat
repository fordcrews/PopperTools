@echo off
setlocal
:: Specify the backup directory
set "backup_dir=%~dp0registry_backup"

:: Restore the registry keys from the backup files
reg import "%backup_dir%\GamePlayer.reg"
reg import "%backup_dir%\Editor.reg"

echo Registry state restored.
endlocal
pause
