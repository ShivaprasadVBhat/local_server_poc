#!/bin/bash
# Setup script for Termux file storage API

echo "Setting up File Storage API for Android..."

# Request storage permission for Termux
termux-setup-storage

echo "Installing required packages..."
pkg update -y
pkg install -y python python-pip

echo "Installing Python dependencies..."
pip install flask flask-cors flask-httpauth werkzeug

echo "Creating storage directory in Downloads..."
DOWNLOADS="/storage/emulated/0/Download/FileStorageAPI"
mkdir -p $DOWNLOADS

echo "Checking access permissions..."
if [ -w "$DOWNLOADS" ]; then
    echo "Storage directory created successfully: $DOWNLOADS"
else
    echo "Warning: Could not create directory in Downloads folder."
    echo "Make sure you've granted Termux storage permissions."
    echo "Falling back to local storage."
fi

echo "Setup completed. Run the application with:"
echo "python app_android.py"