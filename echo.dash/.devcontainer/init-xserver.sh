#!/bin/bash

# Initialize X server, VNC server, and window manager for browser automation
echo "===== Initializing X server environment ====="

# Check if display is already running
if [ -e /tmp/.X11-unix/X1 ]; then
    echo "X server is already running"
    exit 0
fi

# Start Xvfb with better color depth and resolution for browser automation
echo "Starting Xvfb..."
Xvfb :1 -screen 0 1280x1024x24 &
sleep 2

# Start window manager for proper browser rendering
echo "Starting Fluxbox..."
fluxbox -display :1 &
sleep 1

# Start VNC server for remote viewing and debugging
echo "Starting x11vnc..."
x11vnc -display :1 -forever -nopw -shared -bg -o /tmp/x11vnc.log

# Ensure proper permissions for the X socket
chmod 1777 /tmp/.X11-unix
touch /tmp/.Xauthority
chmod 644 /tmp/.Xauthority

echo "X server environment initialized successfully"
echo "You can connect to VNC on port 5901 if needed"