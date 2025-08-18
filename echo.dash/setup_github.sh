#!/bin/bash

# Generate SSH key
ssh-keygen -t ed25519 -C "deep.tree.echo@shells.com" -f ~/.ssh/github_key -N ""

# Start ssh-agent and add the key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_key

# Display the public key to copy to GitHub
echo "Copy this public key to GitHub (https://github.com/settings/ssh/new):"
echo "-------------------"
cat ~/.ssh/github_key.pub
echo "-------------------"

# Initialize git repository
git init

# Configure git
git config --global user.name "Deep Tree Echo"
git config --global user.email "deep.tree.echo@shells.com"

# Add files
git add .

# Create initial commit
git commit -m "Initial commit: Deep Tree Echo project setup"

# Instructions for after adding SSH key to GitHub
echo ""
echo "After adding the SSH key to GitHub:"
echo "1. Create a new repository on GitHub (don't initialize with README)"
echo "2. Run these commands (replace YOUR_REPO with your repository name):"
echo ""
echo "git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git"
echo "git branch -M main"
echo "git push -u origin main"
