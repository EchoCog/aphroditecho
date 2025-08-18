#!/bin/bash
# NanoCog Installation Script

set -e

echo "🚀 Installing NanoCog dependencies..."

# Check if Python 3.10+ is available
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed from requirements.txt"
elif [ -f "pyproject.toml" ]; then
    pip install -e .
    echo "✅ Dependencies installed from pyproject.toml"
else
    echo "❌ Error: No dependency file found (requirements.txt or pyproject.toml)"
    exit 1
fi

echo "🎉 NanoCog installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Navigate to the NanoCog directory: cd NanoCog"
echo "2. Run the server: python server.py"
echo "3. Or run tests: python -m pytest"