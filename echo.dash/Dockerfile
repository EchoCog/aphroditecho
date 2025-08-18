FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV TZ=UTC

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    firefox \
    xvfb \
    sudo \
    wget \
    curl \
    git \
    vim \
    nodejs \
    npm \
    x11vnc \
    xauth \
    tmux \
    htop \
    iotop \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access
RUN useradd -m -s /bin/bash deepecho && \
    echo "deepecho ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up working directory
WORKDIR /home/deepecho/windsurf

# Copy project files
COPY . .

# Fix permissions
RUN chown -R deepecho:deepecho /home/deepecho

# Switch to non-root user
USER deepecho

# Create and activate virtual environment
RUN python3.10 -m venv venv
ENV PATH="/home/deepecho/windsurf/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install firefox

# Configure system limits
RUN echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf && \
    echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Setup Firefox preferences for better performance
RUN mkdir -p /home/deepecho/.mozilla/firefox/deepecho && \
    echo 'user_pref("browser.cache.disk.enable", false);' >> /home/deepecho/.mozilla/firefox/deepecho/user.js && \
    echo 'user_pref("browser.cache.memory.enable", true);' >> /home/deepecho/.mozilla/firefox/deepecho/user.js && \
    echo 'user_pref("browser.cache.memory.capacity", 51200);' >> /home/deepecho/.mozilla/firefox/deepecho/user.js

# Expose VNC port
EXPOSE 5900

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN sudo chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
