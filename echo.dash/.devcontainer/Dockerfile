FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Install required system packages for GUI applications and browser automation
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    python3-tk \
    python3-dev \
    xvfb \
    x11vnc \
    xauth \
    xdotool \
    fluxbox \
    firefox-esr \
    chromium \
    chromium-driver \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    fonts-liberation \
    dbus \
    dbus-x11 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libnss3 \
    libxshmfence1 \
    xdg-utils \
    x11-utils \
    sudo \
    curl \
    gnupg2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for Docker-in-Docker compatibility
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
    && echo "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages in smaller batches for better build stability
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Core dependencies
RUN pip install --no-cache-dir \
    playwright==1.51.0 \
    selenium==4.15.2 \
    python-dotenv==1.0.1

# UI and automation tools
RUN pip install --no-cache-dir \
    pyautogui==0.9.54 \
    pynput==1.8.1 \
    pillow==11.1.0

# Data and service packages
RUN pip install --no-cache-dir \
    psutil>=5.9.0 \
    openai>=1.3.7 \
    beautifulsoup4==4.12.2 \
    websockets>=12.0

# GUI packages
RUN pip install --no-cache-dir \
    matplotlib \
    tkinterdnd2 \
    tkintertable \
    ttkbootstrap \
    tooltip

# Development tools
RUN pip install --no-cache-dir \
    black \
    flake8 \
    pylint

# Special handling for undetected-chromedriver
RUN pip install --no-cache-dir undetected-chromedriver==3.5.3 || echo "Will retry undetected-chromedriver later"

# Install Playwright browsers
RUN mkdir -p /ms-playwright && \
    playwright install --with-deps firefox chromium || echo "Will install browsers in post-start command"

# Set up environment variables for GUI applications
ENV DISPLAY=:1
ENV XAUTHORITY=/tmp/.Xauthority
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONPATH=/workspaces/echosurface
ENV PYTHONUNBUFFERED=1
ENV NODE_OPTIONS=--max_old_space_size=4096

# Create directory for the virtual X display and set permissions
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix && \
    touch /tmp/.Xauthority && chmod 644 /tmp/.Xauthority && \
    mkdir -p /var/run/dbus && chmod 755 /var/run/dbus

# Copy X server initialization script
COPY .devcontainer/init-xserver.sh /usr/local/bin/init-xserver.sh
RUN chmod +x /usr/local/bin/init-xserver.sh

# Copy Docker helper script
COPY .devcontainer/docker-helper.sh /usr/local/bin/docker-helper.sh
RUN chmod +x /usr/local/bin/docker-helper.sh

# Create a wrapper script for environment setup and testing
RUN echo '#!/bin/bash\n\
echo "===== Testing Browser Environment ====="\n\
# Setup display\n\
export DISPLAY=:1\n\
export XAUTHORITY=/tmp/.Xauthority\n\
\n\
# Check if X server is running\n\
if [ -e /tmp/.X11-unix/X1 ]; then\n\
    echo "✓ X server is running"\n\
else\n\
    echo "× X server is not running, starting..."\n\
    /usr/local/bin/init-xserver.sh\n\
fi\n\
\n\
# Test browser\n\
echo "Testing browser launch..."\n\
python -c "import time; from playwright.sync_api import sync_playwright; \\\n\
print(\"Starting Playwright...\"); \\\n\
time.sleep(1); \\\n\
try:\\\n\
    with sync_playwright() as p: \\\n\
        print(\"Launching browser...\"); \\\n\
        browser = p.firefox.launch(headless=False); \\\n\
        print(\"Creating page...\"); \\\n\
        page = browser.new_page(); \\\n\
        print(\"Navigating to example.com...\"); \\\n\
        page.goto(\"https://example.com\"); \\\n\
        print(\"✓ Browser launched successfully!\"); \\\n\
        browser.close()\\\n\
except Exception as e:\\\n\
    print(f\"Error testing browser: {e}\")\\\n\
    print(\"You may need to run: playwright install --with-deps firefox chromium\")\\\n\
"\n\
' > /usr/local/bin/test-browser.sh && \
    chmod +x /usr/local/bin/test-browser.sh

# Create a browser environment checker
RUN echo '#!/bin/bash\n\
echo "==== Browser Environment Diagnostics ===="\n\
echo "Display settings:"\n\
echo "DISPLAY=$DISPLAY"\n\
echo "XAUTHORITY=$XAUTHORITY"\n\
echo "\nChecking X11 socket:"\n\
ls -la /tmp/.X11-unix/\n\
echo "\nChecking running X processes:"\n\
ps aux | grep -E "Xvfb|x11vnc|fluxbox" | grep -v grep\n\
echo "\nChecking browser executables:"\n\
which firefox chromium playwright python\n\
echo "\nStarting minimal X server if needed:"\n\
if [ ! -e /tmp/.X11-unix/X1 ]; then\n\
  echo "X server not running, starting..."\n\
  Xvfb :1 -screen 0 1024x768x16 &\n\
  sleep 2\n\
  echo "Started minimal X server"\n\
else\n\
  echo "X server is already running"\n\
fi\n\
echo "\nChecking Docker setup:"\n\
/usr/local/bin/docker-helper.sh\n\
' > /usr/local/bin/check-browser-env.sh && \
    chmod +x /usr/local/bin/check-browser-env.sh

# Create directories for browser data
RUN mkdir -p /workspaces/echosurface/browser_data \
    /workspaces/echosurface/deep_tree_echo_profile \
    /workspaces/echosurface/activity_logs

# Add vscode user to docker group for Docker-in-Docker access
RUN groupadd -f docker && usermod -aG docker vscode
