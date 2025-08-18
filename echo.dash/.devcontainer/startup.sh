#!/bin/bash
set -e

echo "Starting container services..."

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
sleep 2

# Start VNC server
x11vnc -display :99 -nopw -forever -xkb &

# Keep container running
exec "$@" || tail -f /dev/null