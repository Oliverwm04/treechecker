@echo off
chcp 65001 > nul
title 2026 EUDR Compliance Engine
color 0B

:: NEW: Automatically enters your special environment
call activate forest_env

cd /d "%~dp0"

echo ==========================================
echo   🚀 STARTING GLOBAL BATCH AUDIT
echo ==========================================
python main.py

echo.
echo ==========================================
echo   GENERATING EXECUTIVE DASHBOARD
echo ==========================================
python dashboard.py

echo ==========================================
echo   CLEANUP OPTION
echo ==========================================
set /p del_choice="Would you like to clean up old maps/PDFs now? (y/n): "

:: This version is more strict with the "y" requirement
if /i "%del_choice%"=="y" (
    python clean_workspace.py
) else (
    echo Skipping cleanup. Your files are safe.
)

echo.
echo Audit Cycle Complete.
pause