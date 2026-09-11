@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title FndZlda setup
echo.
echo   FndZlda  -  US Zelda 40th Switch 2 hunter
echo   It's dangerous to go alone! Setting up Python...
echo.

set "BASE=%LOCALAPPDATA%\FndZlda"
set "PYDIR=%BASE%\python"
set "APPDIR=%BASE%\app"
set "PYEXE="

call :find_system_python
if defined PYEXE goto have_python

echo   No Python on PATH. Installing a portable copy under
echo   %PYDIR%
echo.
call :install_embed_python
if defined PYEXE goto have_python

echo   Portable download failed. Trying winget...
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --scope user --disable-interactivity
call :find_system_python
if defined PYEXE goto have_python

echo   Could not install Python.
echo   Download it from https://www.python.org/downloads/windows/
echo   CHECK THE BOX: "Add python.exe to PATH"
echo   then run this file again.
echo.
start "" "https://www.python.org/downloads/windows/"
pause
exit /b 1

:have_python
echo   Using: %PYEXE%
echo   Copying hunter files...
mkdir "%APPDIR%\fndzlda" >nul 2>&1
copy /Y "%~dp0fndzlda\*.py" "%APPDIR%\fndzlda\" >nul
if errorlevel 1 (
  echo   Could not copy fndzlda\*.py — run this from the unzipped repo.
  pause
  exit /b 1
)
copy /Y "%~dp0fndzlda\*.txt" "%APPDIR%\fndzlda\" >nul 2>&1
copy /Y "%~dp0fndzlda\*.wav" "%APPDIR%\fndzlda\" >nul 2>&1
copy /Y "%~dp0fndzlda\*.mp3" "%APPDIR%\fndzlda\" >nul 2>&1
if not exist "%APPDIR%\fndzlda\listen.wav" call :dl "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/listen.wav" "%APPDIR%\fndzlda\listen.wav"
if not exist "%APPDIR%\fndzlda\storms.mp3" call :dl "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/storms.mp3" "%APPDIR%\fndzlda\storms.mp3"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%APPDIR%"
set "PYTHONDONTWRITEBYTECODE=1"
echo   TAKE THIS!
echo.
"%PYEXE%" -m fndzlda %*
exit /b %errorlevel%

:find_system_python
set "PYEXE="
where py >nul 2>&1 && (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)"') do set "PYEXE=%%I"
    exit /b 0
  )
)
where python >nul 2>&1 && (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)"') do set "PYEXE=%%I"
    exit /b 0
  )
)
if exist "%PYDIR%\python.exe" (
  "%PYDIR%\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
  if not errorlevel 1 set "PYEXE=%PYDIR%\python.exe"
)
exit /b 0

:install_embed_python
set "PYEXE="
mkdir "%PYDIR%" >nul 2>&1
set "ZIP=%PYDIR%\python-embed.zip"
call :dl "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip" "%ZIP%" && goto unzip_py
call :dl "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip" "%ZIP%" && goto unzip_py
call :dl "https://www.python.org/ftp/python/3.12.6/python-3.12.6-embed-amd64.zip" "%ZIP%" && goto unzip_py
exit /b 1

:unzip_py
echo   Unpacking portable Python...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PYDIR%' -Force" >nul 2>&1
if errorlevel 1 (
  tar -xf "%ZIP%" -C "%PYDIR%" >nul 2>&1
)
del /q "%ZIP%" >nul 2>&1
mkdir "%PYDIR%\Lib\site-packages" >nul 2>&1
> "%PYDIR%\python312._pth" (
  echo python312.zip
  echo .
  echo Lib
  echo Lib\site-packages
  echo import site
)
if exist "%PYDIR%\python311._pth" copy /Y "%PYDIR%\python312._pth" "%PYDIR%\python311._pth" >nul
if not exist "%PYDIR%\python.exe" exit /b 1
"%PYDIR%\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "PYEXE=%PYDIR%\python.exe"
echo   Portable Python is ready.
exit /b 0

:dl
echo   Downloading %~1
curl.exe -L --fail --retry 3 -A "FndZlda-installer/1.1" -o "%~2" "%~1"
if not errorlevel 1 if exist "%~2" exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%~1' -OutFile '%~2' -UserAgent 'FndZlda-installer/1.1' } catch { exit 1 }"
exit /b %errorlevel%
