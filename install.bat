@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title FndZlda setup
echo.
echo   FndZlda  -  US Zelda 40th Switch 2 hunter
echo   It's dangerous to go alone! Checking Python...
echo.

where py >nul 2>&1
if %errorlevel%==0 goto run_py
where python >nul 2>&1
if %errorlevel%==0 goto run_python

echo   Python is not installed.
echo   Opening https://www.python.org/downloads/
echo   CHECK THE BOX: "Add python.exe to PATH"
echo   then run this file again.
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:run_py
echo   TAKE THIS!
echo.
py -3 -m fndzlda %*
exit /b %errorlevel%

:run_python
echo   TAKE THIS!
echo.
python -m fndzlda %*
exit /b %errorlevel%
