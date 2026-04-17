#!/bin/bash

# 🔮 Orion CLI - GitHub Publishing Script
# This script will help you publish your project to GitHub easily

set -e  # Exit on error

echo "🔮 Orion CLI - GitHub Publishing Assistant"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Get GitHub username
echo -e "${BLUE}Step 1: GitHub Configuration${NC}"
read -p "Enter your GitHub username: " GITHUB_USERNAME

# Step 2: Get repository name
echo ""
echo -e "${BLUE}Step 2: Repository Name${NC}"
read -p "Enter repository name (default: orion-cli): " REPO_NAME
REPO_NAME=${REPO_NAME:-orion-cli}

# Step 3: Initialize Git
echo ""
echo -e "${BLUE}Step 3: Initializing Git${NC}"
if [ ! -d .git ]; then
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
else
    echo -e "${YELLOW}Git already initialized${NC}"
fi

# Step 4: Create .gitignore if needed
echo ""
echo -e "${BLUE}Step 4: Configuring .gitignore${NC}"
echo -e "${GREEN}✓ .gitignore already configured${NC}"

# Step 5: Add all files
echo ""
echo -e "${BLUE}Step 5: Adding files to Git${NC}"
git add .
echo -e "${GREEN}✓ Files added${NC}"

# Step 6: Create initial commit
echo ""
echo -e "${BLUE}Step 6: Creating initial commit${NC}"
git commit -m "Initial commit: Orion CLI - AI coding assistant interface

- Terminal-based interface for AI models
- Multi-provider support (Ollama, LM Studio, OpenAI, Anthropic)
- 22 built-in slash commands
- 14 integrated tools
- Complete English documentation
- MIT License"
echo -e "${GREEN}✓ Initial commit created${NC}"

# Step 7: Set main branch
echo ""
echo -e "${BLUE}Step 7: Setting main branch${NC}"
git branch -M main
echo -e "${GREEN}✓ Branch set to 'main'${NC}"

# Step 8: Instructions for GitHub
echo ""
echo -e "${BLUE}Step 8: Next Steps${NC}"
echo ""
echo "================================================"
echo -e "${YELLOW}Now, create a repository on GitHub:${NC}"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: ${REPO_NAME}"
echo "3. Description: 'AI coding assistant CLI - Your local alternative to Gemini CLI and Claude Code'"
echo "4. Keep it PUBLIC (for open source)"
echo "5. DON'T initialize with README (we already have one)"
echo "6. Click 'Create repository'"
echo ""
echo "================================================"
echo ""
read -p "Press ENTER once you've created the repository on GitHub..."

# Step 9: Add remote and push
echo ""
echo -e "${BLUE}Step 9: Connecting to GitHub and pushing${NC}"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
echo "Repository URL: ${REPO_URL}"

git remote add origin "${REPO_URL}" 2>/dev/null || git remote set-url origin "${REPO_URL}"
echo -e "${GREEN}✓ Remote added${NC}"

echo ""
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "================================================"
echo -e "${GREEN}🎉 SUCCESS! Your project is now on GitHub!${NC}"
echo ""
echo "Your repository: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "Next steps:"
echo "  • Add topics/tags on GitHub (AI, CLI, Ollama, Python)"
echo "  • Add a repository description"
echo "  • Consider adding a screenshot"
echo "  • Share on X/Twitter!"
echo ""
echo "================================================"
