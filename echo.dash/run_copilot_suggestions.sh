#!/bin/bash
# Run copilot_suggestions.py with the necessary environment variables

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
fi

# Check if GITHUB_TOKEN is set, and if not, prompt for it
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN environment variable is not set."
    echo "Please enter your GitHub token (it will not be saved):"
    read -s GITHUB_TOKEN
    echo ""
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "No token provided. Exiting."
        exit 1
    fi
fi

# Export the token so the Python script can access it
export GITHUB_TOKEN

# Run the script
python copilot_suggestions.py

# Clear the token from the environment for security
unset GITHUB_TOKEN
