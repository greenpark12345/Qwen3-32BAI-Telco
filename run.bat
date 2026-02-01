@echo off
chcp 65001 >nul
title 5G Network Problem Diagnosis Solver

echo.
echo +================================================================+
echo ^|         5G Network Problem Diagnosis Solver v1.0               ^|
echo +================================================================+
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

:: Switch to script directory
cd /d "%~dp0"

:: Check for necessary files
if not exist "config.txt" (
    echo [Error] Configuration file config.txt missing
    pause
    exit /b 1
)

:: Run main program
echo Starting solver...
echo.
python main.py

echo.
echo Program execution completed, press any key to exit...
pause >nul
