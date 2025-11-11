./deploy.sh#!/bin/bash
# Deployment script for BNB Profit Harvester Bot

set -e

echo "🚀 Deploying BNB Profit Harvester Bot (Improved Version)..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "   Please create .env file with your API keys and configuration."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running!"
    echo "   Please start Docker and try again."
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo ""

# Build the Docker image
echo "📦 Building Docker image..."
docker compose build

echo ""
echo "🛑 Stopping existing bot (if running)..."
docker compose down

echo ""
echo "🚀 Starting bot..."
docker compose up -d

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 View logs with: docker compose logs -f"
echo "🛑 Stop bot with: docker compose down"
echo "🔄 Restart bot with: docker compose restart"
echo ""
echo "Checking bot status..."
sleep 2
docker compose ps

