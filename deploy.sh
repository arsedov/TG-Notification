#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment..."

# Pull latest changes from git
echo "📥 Pulling latest changes from Git..."
git pull origin main

# Rebuild and restart containers
echo "🛠 Rebuilding and restarting containers..."
docker compose up -d --build

# Clean up unused images to save space on VPS
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment successful!"
