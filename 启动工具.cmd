@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0code"
set "VERAN_PYTHON=python"
if exist "%USERPROFILE%\miniconda3\python.exe" set "VERAN_PYTHON=%USERPROFILE%\miniconda3\python.exe"
echo Starting VERAN. The browser will open automatically.
"%VERAN_PYTHON%" -m veran_advisor.demo %*
if errorlevel 1 pause
