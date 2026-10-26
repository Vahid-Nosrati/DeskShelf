@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\package_release.py
if errorlevel 1 goto fail
echo Release files are in the release folder. Personal data was excluded.
pause
exit /b 0
:fail
echo Packaging failed. Read the error above.
pause
exit /b 1
