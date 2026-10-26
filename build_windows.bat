@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto fail
)
set "DESKSHELF_PY=.venv\Scripts\python.exe"
echo Using isolated Python:
"%DESKSHELF_PY%" --version
if not defined DESKSHELF_INDEX_URL set "DESKSHELF_INDEX_URL=https://pypi.org/simple"
if exist "wheelhouse\*.whl" (
    "%DESKSHELF_PY%" -m pip install --no-index --find-links wheelhouse -r requirements.txt
    if errorlevel 1 goto fail
) else (
    "%DESKSHELF_PY%" -m pip install --index-url "%DESKSHELF_INDEX_URL%" --timeout 120 --retries 2 --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Trying the Tsinghua PyPI mirror...
        "%DESKSHELF_PY%" -m pip install --index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --timeout 120 --retries 2 --disable-pip-version-check -r requirements.txt
        if errorlevel 1 goto fail
    )
)
"%DESKSHELF_PY%" scripts\collect_notices.py
if errorlevel 1 goto fail
"%DESKSHELF_PY%" -m PyInstaller --noconfirm --clean --windowed --onedir --name DeskShelf --icon assets\deskshelf.ico --add-data "assets;assets" --add-data "locales;locales" --add-data "help;help" --add-data "LICENSE;." --add-data "THIRD_PARTY_NOTICES.md;." --add-data "licenses;licenses" main.py
if errorlevel 1 goto fail
for %%F in (app_info.json README.md README_FA.md LICENSE THIRD_PARTY_NOTICES.md BUILD_INFO.json CONTRIBUTORS CONTRIBUTING.md CHANGELOG.md) do (
    copy /Y "%%F" "dist\DeskShelf\%%F" >nul
    if errorlevel 1 goto fail
)
for %%D in (licenses third_party_licenses locales help docs) do (
    xcopy /E /I /Y "%%D" "dist\DeskShelf\%%D" >nul
    if errorlevel 1 goto fail
)
echo.
echo Build successful: dist\DeskShelf\DeskShelf.exe
echo Keep the entire DeskShelf folder, not only the EXE.
echo To prepare public ZIPs, run package_release.bat.
pause
exit /b 0
:fail
echo.
echo Build failed. Please copy the last error lines for troubleshooting.
pause
exit /b 1
