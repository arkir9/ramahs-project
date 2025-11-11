#!/bin/bash
# Render Deployment Script for BNB Profit Harvester Bot
# This script helps set up and deploy the bot to Render

set -e

echo "🚀 Render Deployment Setup for BNB Profit Harvester Bot"
echo "========================================================"
echo ""

# Check if render.yaml exists
if [ ! -f render.yaml ]; then
    echo "❌ ERROR: render.yaml not found!"
    echo "   Please ensure render.yaml exists in the project root."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "❌ ERROR: requirements.txt not found!"
    exit 1
fi

# Check if main.py exists
if [ ! -f main.py ]; then
    echo "❌ ERROR: main.py not found!"
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo ""

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo "📦 Render CLI not found. Installing instructions:"
    echo "   Visit: https://render.com/docs/cli"
    echo "   Or use: npm install -g render-cli"
    echo ""
    echo "   Alternatively, you can deploy via Render Dashboard:"
    echo "   1. Go to https://dashboard.render.com"
    echo "   2. Click 'New +' -> 'Background Worker'"
    echo "   3. Connect your GitHub repository"
    echo "   4. Configure the service as specified in render.yaml"
    echo "   5. Add environment variables (see RENDER_DEPLOYMENT.md)"
    echo ""
else
    echo "✅ Render CLI found"
    echo ""
    echo "To deploy using CLI:"
    echo "  1. Login: render login"
    echo "  2. Deploy: render deploy"
    echo ""
fi

echo "📋 Required Environment Variables:"
echo "=================================="
echo ""
echo "Required:"
echo "  - BINANCE_API_KEY: Your Binance API key"
echo "  - BINANCE_API_SECRET: Your Binance API secret"
echo ""
echo "Optional (with defaults):"
echo "  - TESTNET: Use Binance testnet (true/false, default: false)"
echo "  - TELEGRAM_BOT_TOKEN: Telegram bot token for notifications"
echo "  - TELEGRAM_CHAT_ID: Telegram chat ID for notifications"
echo "  - SYMBOL: Trading pair (default: BNBUSDT)"
echo "  - CHECK_INTERVAL: Check interval in seconds (default: 5)"
echo "  - TARGET_PCT: Target profit percentage (default: 0.005 = 0.5%)"
echo "  - STOP_LOSS_PCT: Stop loss percentage (default: 0.10 = 10%)"
echo "  - DRY_RUN: Run in dry-run mode (true/false, default: true)"
echo "  - QUANTITY_DECIMALS: Quantity decimals (default: 6)"
echo "  - MIN_NOTIONAL: Minimum notional value (default: 1.0)"
echo "  - ATR_MULTIPLIER: ATR multiplier for stop loss (default: 1.5)"
echo "  - USE_ATR_STOP_LOSS: Use ATR-based stop loss (true/false, default: true)"
echo "  - REENTRY_STRATEGY: Re-entry strategy (none/immediate/limit_ladder, default: none)"
echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Push this code to GitHub"
echo "2. Go to https://dashboard.render.com"
echo "3. Click 'New +' -> 'Background Worker'"
echo "4. Connect your GitHub repository: git@github.com:arkir9/ramahs-project.git"
echo "5. Render will detect render.yaml automatically"
echo "6. Add environment variables in the Render Dashboard"
echo "7. Deploy!"
echo ""
echo "📚 For more information, see RENDER_DEPLOYMENT.md"
echo ""

