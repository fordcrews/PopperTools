@echo off
setlocal
:: Create a backup directory
set "backup_dir=%~dp0registry_backup"
if not exist "%backup_dir%" mkdir "%backup_dir%"

:: Save the state of the registry keys
reg export "HKCU\Software\Future Pinball\GamePlayer" "%backup_dir%\GamePlayer.reg" /y
reg export "HKCU\Software\Future Pinball\Editor" "%backup_dir%\Editor.reg" /y

echo Registry state saved.
endlocal

