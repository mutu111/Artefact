@echo off
chcp 65001 >nul
cd /d "%~dp0runtime"
if exist "%USERPROFILE%\miniconda3\python.exe" (
  "%USERPROFILE%\miniconda3\python.exe" -m veran_advisor.demo
) else (
  python -m veran_advisor.demo
)
if errorlevel 1 pause
