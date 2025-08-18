#!/bin/bash

# Manual trigger script for EchoPilot workflow
# This script simulates the GitHub Actions workflow locally

echo "🚀 Manual EchoPilot Trigger"
echo "=========================="
echo "This script will run the EchoPilot analysis and show what issues would be created."
echo ""

# Check if we're in the right directory
if [ ! -f ".github/workflows/echopilot.yml" ]; then
    echo "❌ Error: echopilot.yml workflow not found!"
    echo "Please run this script from the repository root."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    exit 1
fi

echo "✅ Environment check passed"
echo ""

# Run the manual trigger script
echo "🔍 Running EchoPilot analysis..."
python3 trigger_echopilot.py

echo ""
echo "🎯 To fix the GitHub Actions workflow:"
echo "1. The workflow should now work with the updated syntax"
echo "2. You can manually trigger it from the GitHub Actions tab"
echo "3. Or wait for the scheduled run (every 6 hours)"
echo ""
echo "💡 If you want to test the workflow immediately:"
echo "   - Go to your repository on GitHub"
echo "   - Click on 'Actions' tab"
echo "   - Find 'EchoPilot Self-Improvement Workflow'"
echo "   - Click 'Run workflow' button"
echo ""