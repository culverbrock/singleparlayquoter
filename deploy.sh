#!/bin/bash

# Single Parlay Quoter - Quick Deploy Script

echo "🚀 Single Parlay Quoter - Deployment Helper"
echo "==========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo ""
fi

# Add all files
echo "📁 Adding files to git..."
git add .
echo ""

# Commit
echo "💾 Creating commit..."
read -p "Enter commit message (or press enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update Single Parlay Quoter"
fi
git commit -m "$commit_msg"
echo ""

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "🔗 Setting up GitHub remote..."
    echo ""
    echo "Please create a new repository on GitHub first:"
    echo "👉 https://github.com/new"
    echo ""
    read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): " repo_url
    git remote add origin "$repo_url"
    echo ""
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git branch -M main
git push -u origin main
echo ""

echo "✅ Code pushed to GitHub!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://railway.app"
echo "2. Sign in with GitHub"
echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
echo "4. Select your repository"
echo "5. Wait 2-3 minutes for deployment"
echo "6. Get your public URL from Railway dashboard"
echo ""
echo "🎉 That's it! Share your URL with anyone who wants to use it!"
echo ""

