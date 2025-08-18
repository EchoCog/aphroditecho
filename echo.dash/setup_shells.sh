#!/bin/bash

# Exit on error
set -e

echo "Setting up Deep Tree Echo environment on Shells.com..."

# Configure system limits for better resource management
sudo tee /etc/security/limits.d/deepecho.conf << EOF
deepecho soft nproc 2048
deepecho hard nproc 4096
deepecho soft nofile 8192
deepecho hard nofile 16384
EOF

# Update system
sudo apt-get update

# Install system dependencies (minimal set)
sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    firefox \
    git \
    vim \
    nodejs \
    npm \
    xvfb \
    x11vnc \
    curl \
    wget \
    htop \
    tmux \
    screen \
    gnome-keyring \
    libsecret-1-0 \
    libsecret-1-dev \
    dbus-x11

# Set up Python aliases
echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc

# Start dbus for keyring
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax)
fi

# Initialize keyring (will use D33ptr333ch0 as password)
echo "D33ptr333ch0" | gnome-keyring-daemon --unlock
export $(gnome-keyring-daemon --start)

# Configure swap for better memory management
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Create Deep Tree Echo user
if ! id -u deepecho &>/dev/null; then
    sudo useradd -m -s /bin/bash deepecho
    sudo usermod -aG sudo deepecho
    echo "deepecho ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/deepecho
fi

# Set up project directory and permissions
sudo mkdir -p /opt/deepecho
sudo chown -R deepecho:deepecho /opt/deepecho

# Create and activate virtual environment with proper permissions
sudo -u deepecho python3 -m venv /opt/deepecho/venv
source /opt/deepecho/venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install keyring secretstorage dbus-python

# Clone the repository (if not already done)
if [ ! -d "/opt/deepecho/windsurf-project" ]; then
    cd /opt/deepecho
    sudo -u deepecho git clone https://github.com/EchoCog/windsurf-project.git
fi

# Set proper ownership of the project directory
sudo chown -R deepecho:deepecho /opt/deepecho/windsurf-project

# Create screen session configuration
cat > /opt/deepecho/.screenrc << EOF
# Screen configuration for Deep Tree Echo
startup_message off
defscrollback 10000
hardstatus alwayslastline
hardstatus string '%{= kG}[ %{G}%H %{g}][%= %{= kw}%?%-Lw%?%{r}(%{W}%n*%f%t%?(%u)%?%{r})%{w}%?%+Lw%?%?%= %{g}][%{B} %m-%d %{W}%c %{g}]'

# Default screens
screen -t monitor 0 python3 monitor.py
screen -t logs 1 tail -f /var/log/syslog
screen -t htop 2 htop
EOF

# Set proper ownership of screen config
sudo chown deepecho:deepecho /opt/deepecho/.screenrc

# Add keyring environment variables to bashrc
echo 'export $(gnome-keyring-daemon --start)' >> ~/.bashrc
echo 'export SSH_AUTH_SOCK' >> ~/.bashrc

echo "Deep Tree Echo environment setup complete!"
echo ""
echo "Keyring is initialized with password: D33ptr333ch0"
echo ""
echo "To start monitoring, run:"
echo "screen -S monitor python3 monitor.py"
echo ""
echo "Or use the pre-configured screen session:"
echo "screen -c /opt/deepecho/.screenrc"
