# Deployment Notes - Improved Bot Version

## ✅ What Changed

The bot has been upgraded to `main_improved.py` with the following enhancements:

1. **ATR-Based Trailing Stop Loss** - Dynamic stop loss based on volatility
2. **Dynamic Profit Targets** - Adjusts based on market volatility
3. **Exchange Filter Validation** - Proper handling of step sizes and min notional
4. **Telegram Notifications** - Only for trade events (no spam)
5. **Re-entry Strategies** - Optional re-entry after profit harvest
6. **Decimal Precision** - Uses Decimal for all financial calculations
7. **Better Error Handling** - More robust API calls and error recovery

## 🔧 New Environment Variables

Add these to your `.env` file (optional, defaults shown):

```bash
# ATR Configuration
USE_ATR_STOP_LOSS=true          # Enable ATR-based trailing stop loss
ATR_MULTIPLIER=1.5              # ATR multiplier for stop loss (default: 1.5)

# Re-entry Strategy
REENTRY_STRATEGY=none           # Options: none, fixed_fraction, limit_ladder
REENTRY_FRACTION=0.5            # Fraction of proceeds to use for re-entry (0.5 = 50%)
LADDER_ORDERS=5                 # Number of limit orders for ladder strategy
LADDER_SPACING_MULTIPLIER=0.15  # Spacing between ladder orders
```

## 📋 Existing Variables (Still Required)

```bash
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TESTNET=false
DRY_RUN=true                    # Set to false for live trading

SYMBOL=BNBUSDT
TARGET_PCT=0.005                # 0.5% profit target
STOP_LOSS_PCT=0.10              # 10% portfolio stop loss
CHECK_INTERVAL=5                # Seconds between price checks

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🚀 Deployment Steps

### 1. Update .env (if needed)
Add the new optional variables if you want to customize ATR or re-entry behavior.

### 2. Build and Deploy with Docker
```bash
# Build the new image
docker compose build

# Start the bot
docker compose up -d

# Check logs
docker compose logs -f
```

### 3. Verify Deployment
```bash
# Check if container is running
docker ps | grep bnb-bot

# View logs
docker compose logs bnb-bot

# Restart if needed
docker compose restart
```

## 🔍 Key Features

### ATR-Based Stop Loss
- Calculates Average True Range (ATR) from 5-minute candles
- Sets trailing stop loss at `entry_price - (ATR_MULTIPLIER * ATR)`
- Updates stop loss as price moves up (trailing behavior)
- Refreshes ATR every 5 minutes

### Dynamic Profit Targets
- Base target: `TARGET_PCT` (default 0.5%)
- If ATR is enabled: Uses `max(TARGET_PCT, ATR_PCT/2)`
- Adapts to market volatility

### Re-entry Strategies
- **none**: No re-entry (default)
- **fixed_fraction**: Buy back a fraction of proceeds if price drops 2% after harvest
- **limit_ladder**: Place multiple limit orders (not fully implemented)

## ⚠️ Important Notes

1. **DRY_RUN**: Always test with `DRY_RUN=true` first!
2. **API Keys**: Ensure your IP is whitelisted in Binance
3. **Balance**: Bot needs BNB balance to start trading
4. **Notifications**: Telegram notifications only sent for trades
5. **Stop Loss**: Bot exits after stop loss is triggered (both ATR and portfolio)

## 🐛 Troubleshooting

### Bot exits immediately
- Check if you have BNB balance
- Verify API keys are correct
- Check IP whitelist in Binance

### ATR calculation fails
- Bot will disable ATR and use fixed percentage stop loss
- Check API connection and symbol availability

### No trades executed
- Verify `DRY_RUN=false` for live trading
- Check if profit target is reached
- Ensure minimum notional requirements are met

## 📊 Monitoring

Monitor the bot via:
1. Docker logs: `docker compose logs -f`
2. Telegram notifications (trade events only)
3. Bot log file: `bot.log` (if volume mounted)

## 🔄 Rollback

If you need to rollback to the previous version:
```bash
# Restore backup
cp main.py.backup_* main.py

# Rebuild and restart
docker compose build
docker compose restart
```

