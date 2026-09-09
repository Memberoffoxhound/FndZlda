@echo off
setlocal
cd /d "%~dp0"
py -3 -m fndzlda %*
if errorlevel 9009 python -m fndzlda %*
