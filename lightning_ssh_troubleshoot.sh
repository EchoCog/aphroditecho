#!/bin/bash
# Lightning AI SSH Connection Troubleshooting Script
# For Personal Developer Studio instances

echo "🔧 Lightning AI SSH Connection Troubleshooting"
echo "=============================================="

# Check SSH connection with verbose output
echo "1️⃣ Testing SSH connection with verbose logging..."
ssh -v s_01k38606vyrx8vgc38h5wm9rd9@ssh.lightning.ai -o ConnectTimeout=30 -o ServerAliveInterval=60 -o ServerAliveCountMax=3

# If that fails, try with different SSH options
if [ $? -ne 0 ]; then
    echo ""
    echo "2️⃣ Trying with alternative SSH options..."
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 s_01k38606vyrx8vgc38h5wm9rd9@ssh.lightning.ai
fi

# If still fails, try with keep-alive
if [ $? -ne 0 ]; then
    echo ""
    echo "3️⃣ Trying with keep-alive settings..."
    ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=5 -o TCPKeepAlive=yes s_01k38606vyrx8vgc38h5wm9rd9@ssh.lightning.ai
fi
