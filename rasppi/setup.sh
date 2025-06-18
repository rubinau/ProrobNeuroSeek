#!/bin/bash

# ==============================================================================
# Setup Script for the Missing Item Finder Robot (Simplified Offline Version)
# ==============================================================================
# This script automates the setup of the Python environment and downloads
# the necessary assets. It assumes you have already provided the static
# CSS file at 'static/css/tailwind.css'.
#
# To run this script:
# 1. Make it executable:  chmod +x setup.sh
# 2. Run it:              ./setup.sh
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Introduction ---
echo "--- Starting Simplified Offline Environment Setup for Finder Robot ---"

# --- Step 1: Check for Prerequisites ---
echo -e "\n[Step 1/4] Checking for prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 could not be found. Please install Python 3."
    exit 1
fi
if ! command -v curl &> /dev/null; then
    echo "ERROR: curl could not be found. Please install curl (e.g., 'sudo apt-get install curl')."
    exit 1
fi
echo "Prerequisites found."

# --- Step 2: Create Python Virtual Environment ---
VENV_DIR="venv"
echo -e "\n[Step 2/4] Creating Python virtual environment in './${VENV_DIR}'..."
if [ -d "$VENV_DIR" ]; then
    echo "Python virtual environment already exists. Skipping creation."
else
    python3 -m venv $VENV_DIR
    echo "Virtual environment created."
fi

# --- Step 3: Install Python Dependencies ---
echo -e "\n[Step 3/4] Activating virtual environment and installing Python packages..."
source $VENV_DIR/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "All Python packages installed successfully."

# --- Step 4: Download Offline JavaScript Assets ---
STATIC_DIR="${PWD}/src/templates/static"
JS_DIR="${STATIC_DIR}/js"
echo -e "\n[Step 4/4] Downloading offline JavaScript assets..."
mkdir -p $JS_DIR
SOCKET_IO_URL="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.4/socket.io.js"
curl -o "${JS_DIR}/socket.io.js" -L $SOCKET_IO_URL
echo "Socket.IO client downloaded."

# The SpaCy model will be downloaded by the main script on first run if not found.
echo -e "\nSetup Complete!"
echo "========================================================"
echo "Your environment is ready for OFFLINE use."
echo ""
echo "IMPORTANT: Make sure you have created the file 'static/css/tailwind.css' and pasted your generated CSS into it."
echo ""
echo "To run the application, follow these steps:"
echo "1. Activate the virtual environment: source ${VENV_DIR}/bin/activate"
echo "2. Run the main application:       python3 app.py"
echo ""
echo "You can then access the web interface at http://<your_ip>:5000"
echo "========================================================"
```text
