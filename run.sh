#!/bin/bash
# 5G Network Problem Diagnosis Solver Startup Script

echo ""
echo "+================================================================+"
echo "|         5G Network Problem Diagnosis Solver v1.0               |"
echo "+================================================================+"
echo ""

# Switch to script directory
cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python3 not found, please ensure it is installed"
    exit 1
fi

# Check configuration file
if [ ! -f "config.txt" ]; then
    echo "[Error] Configuration file config.txt missing"
    exit 1
fi

# Run main program
echo "Starting solver..."
echo ""
python3 main.py

echo ""
echo "Program execution completed"
