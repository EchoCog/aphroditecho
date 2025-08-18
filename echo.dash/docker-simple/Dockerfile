FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV TZ=UTC

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access
RUN useradd -m -s /bin/bash deepecho && \
    echo "deepecho ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up working directory
WORKDIR /home/deepecho/windsurf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER deepecho

# Create virtual environment directory
RUN mkdir -p /home/deepecho/.mozilla/firefox/deepecho

# Expose VNC port
EXPOSE 5900

ENTRYPOINT ["/docker-entrypoint.sh"]