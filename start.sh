#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check for restart flag
RESTART=false
if [[ "$1" == "--restart" ]] || [[ "$1" == "-r" ]]; then
    RESTART=true
fi

# Check if server is already running on port 7234
PID=$(lsof -Pi :7234 -sTCP:LISTEN -t 2>/dev/null)

if [ -n "$PID" ]; then
    if [ "$RESTART" = true ]; then
        echo "Killing existing server (PID: $PID)..."
        kill $PID
        sleep 1
    else
        echo "Server is already running on port 7234 (PID: $PID)"
        echo "Visit: http://localhost:7234"
        echo "Use --restart or -r flag to restart the server"
        exit 0
    fi
fi

# Activate virtual environment and start the Flask server
echo "Starting server on port 7234..."
source "$SCRIPT_DIR/venv/bin/activate"
python "$SCRIPT_DIR/app.py"
