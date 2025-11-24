#!/bin/bash
# run.sh
# Ensures environment setup, then launches the automation

echo "🚀 Starting AI WordPress automation..."

# Activate Python virtual environment if applicable
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure data directories exist
python3 setup_directories.py

# Start main loop
python3 main.py
