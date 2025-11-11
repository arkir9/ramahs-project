# Render Deployment Guide

This guide explains how to deploy the BNB Profit Harvester Bot to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. GitHub repository with your code
3. Binance API credentials
4. (Optional) Telegram bot token and chat ID for notifications

## Deployment Methods

### Method 1: Using Render Dashboard (Recommended)

1. **Create a New Background Worker**
   - Go to https://dashboard.render.com
   - Click "New +" → "Background Worker"
   - Connect your GitHub repository: `git@github.com:arkir9/ramahs-project.git`

2. **Configure the Service**
   - Render will automatically detect `render.yaml` if present
   - Or manually configure:
     - **Name**: `bnb-profit-harvester-bot`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py`
     - **Plan**: Starter (or higher for production)

3. **Set Environment Variables**
   - Go to the "Environment" tab
   - Add the following variables:

   **Required:**
   ```
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_api_secret_here
   ```

   **Optional (with defaults):**
   ```
   TESTNET=false
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   SYMBOL=BNBUSDT
   CHECK_INTERVAL=5
   TARGET_PCT=0.005
   STOP_LOSS_PCT=0.10
   DRY_RUN=true
   QUANTITY_DECIMALS=6
   MIN_NOTIONAL=1.0
   ATR_MULTIPLIER=1.5
   USE_ATR_STOP_LOSS=true
   REENTRY_STRATEGY=none
   ```

4. **Deploy**
   - Click "Create Background Worker"
   - Render will build and deploy your bot
   - Check logs to ensure it's running correctly

### Method 2: Using Render CLI

1. **Install Render CLI**
   ```bash
   npm install -g render-cli
   ```

2. **Login to Render**
   ```bash
   render login
   ```

3. **Deploy**
   ```bash
   render deploy
   ```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Your Binance API key | `your_api_key_here` |
| `BINANCE_API_SECRET` | Your Binance API secret | `your_api_secret_here` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `TESTNET` | Use Binance testnet | `false` | `true` or `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - | `123456:ABC-DEF` |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | - | `123456789` |
| `SYMBOL` | Trading pair | `BNBUSDT` | `BNBUSDT` |
| `CHECK_INTERVAL` | Check interval (seconds) | `5` | `5` |
| `TARGET_PCT` | Target profit percentage | `0.005` | `0.005` (0.5%) |
| `STOP_LOSS_PCT` | Stop loss percentage | `0.10` | `0.10` (10%) |
| `DRY_RUN` | Run in dry-run mode | `true` | `true` or `false` |
| `QUANTITY_DECIMALS` | Quantity decimals | `6` | `6` |
| `MIN_NOTIONAL` | Minimum notional value | `1.0` | `1.0` |
| `ATR_MULTIPLIER` | ATR multiplier for stop loss | `1.5` | `1.5` |
| `USE_ATR_STOP_LOSS` | Use ATR-based stop loss | `true` | `true` or `false` |
| `REENTRY_STRATEGY` | Re-entry strategy | `none` | `none`, `immediate`, `limit_ladder` |

## Monitoring

### View Logs

1. Go to your service in Render Dashboard
2. Click on "Logs" tab
3. Real-time logs will be displayed

### Check Status

- Service status is shown in the Render Dashboard
- Green indicator means the service is running
- Check logs if the service fails to start

## Troubleshooting

### Bot Not Starting

1. **Check Logs**: Review the logs in Render Dashboard for errors
2. **Verify Environment Variables**: Ensure all required variables are set
3. **Check API Keys**: Verify Binance API keys are correct and have proper permissions
4. **Test Locally**: Run the bot locally first to identify issues

### Common Issues

1. **Missing Environment Variables**: Ensure all required variables are set
2. **API Connection Issues**: Check if Binance API is accessible from Render
3. **Python Version**: Ensure Python 3.12 is available (configured in render.yaml)
4. **Dependencies**: Check if all dependencies in requirements.txt are correct

## Cost Considerations

- **Starter Plan**: $7/month (suitable for testing)
- **Standard Plan**: $25/month (recommended for production)
- Check Render pricing for latest information: https://render.com/pricing

## Security Best Practices

1. **Never commit API keys**: Keep them in Render environment variables only
2. **Use Testnet First**: Test with `TESTNET=true` before going live
3. **Enable Dry Run**: Start with `DRY_RUN=true` to test without real trades
4. **Monitor Logs**: Regularly check logs for suspicious activity
5. **Limit API Permissions**: Only grant necessary permissions to API keys

## Updating the Bot

1. **Push to GitHub**: Push your changes to the repository
2. **Auto-Deploy**: Render will automatically detect changes and redeploy
3. **Manual Deploy**: Or manually trigger deployment from Render Dashboard

## Support

- Render Documentation: https://render.com/docs
- Render Support: https://render.com/support
- Project Repository: https://github.com/arkir9/ramahs-project

