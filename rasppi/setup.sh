#!/bin/bash

# ==============================================================================
# Setup Script for the Missing Item Finder Robot (Fully Offline Version)
# ==============================================================================
# This script automates the setup of the Python environment AND the necessary
# Node.js tools to build an optimized CSS file for the web interface.
#
# To run this script:
# 1. Make it executable:  chmod +x setup.sh
# 2. Run it:              ./setup.sh
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Introduction ---
echo "--- Starting Full Offline Environment Setup for Finder Robot ---"

# --- Step 1: Check for Prerequisites ---
echo -e "\n[Step 1/7] Checking for prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 could not be found. Please install Python 3."
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm (Node.js) could not be found. Please install Node.js and npm."
    exit 1
fi
if ! command -v curl &> /dev/null; then
    echo "ERROR: curl could not be found. Please install curl (e.g., 'sudo apt-get install curl')."
    exit 1
fi
echo "Prerequisites found."

# --- Step 2: Create Python Virtual Environment ---
VENV_DIR="venv"
echo -e "\n[Step 2/7] Creating Python virtual environment in './${VENV_DIR}'..."
if [ -d "$VENV_DIR" ]; then
    echo "Python virtual environment already exists. Skipping creation."
else
    python3 -m venv $VENV_DIR
    echo "Virtual environment created."
fi

# --- Step 3: Install Python Dependencies ---
echo -e "\n[Step 3/7] Activating virtual environment and installing Python packages..."
source $VENV_DIR/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "All Python packages installed successfully."

# --- Step 4: Download Offline JavaScript Assets ---
STATIC_DIR="${PWD}/static"
JS_DIR="${STATIC_DIR}/js"
echo -e "\n[Step 4/7] Downloading offline JavaScript assets..."
mkdir -p $JS_DIR
SOCKET_IO_URL="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.4/socket.io.js"
curl -o "${JS_DIR}/socket.io.js" -L $SOCKET_IO_URL
echo "Socket.IO client downloaded."

# --- Step 5: Setup and Build Offline CSS ---
CSS_DIR="${STATIC_DIR}/css"
CSS_INPUT_FILE="${CSS_DIR}/input.css"
CSS_OUTPUT_FILE="${CSS_DIR}/output.css"
TAILWIND_CONFIG_FILE="tailwind.config.js"

echo -e "\n[Step 5/7] Setting up and building offline CSS with Tailwind..."
mkdir -p $CSS_DIR

# FIX: Explicitly install the latest stable V3 of Tailwind CSS for compatibility.
echo "Installing Tailwind CSS v3..."
npm install -D `tailwind`css@3

# Create the Tailwind CSS config file. This structure is correct for v3.
echo "Creating ${TAILWIND_CONFIG_FILE}..."
cat <<EOF > $TAILWIND_CONFIG_FILE
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

# Create the source CSS input file
echo "Creating source CSS file..."
cat <<EOF > $CSS_INPUT_FILE
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

# Run the Tailwind build process with the --minify flag for an optimized output.
echo "Building and minifying the final CSS file..."
npx tailwindcss -i $CSS_INPUT_FILE -o $CSS_OUTPUT_FILE --minify
echo "Optimized offline CSS file created at ${CSS_OUTPUT_FILE}"

# --- Step 6: Download the SpaCy NLP Model ---
echo -e "\n[Step 6/7] Downloading the SpaCy NLP model (en_core_web_md)..."
python3 -m spacy download en_core_web_md
echo "SpaCy model downloaded successfully."

# --- Step 7: Final Instructions ---
echo -e "\n[Step 7/7] Setup Complete!"
echo "========================================================"
echo "Your environment is ready for FULLY OFFLINE use."
echo ""
echo "To run the application, follow these steps:"
echo "1. Activate the virtual environment: source ${VENV_DIR}/bin/activate"
echo "2. Run the main application:       python3 app.py"
echo ""
echo "You can then access the web interface at http://<your_ip>:5000"
echo "========================================================"
```text
