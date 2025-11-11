# 🚀 BNB Trading Bot - Quick Start

## ✅ All Features Working!

Your bot is fully configured with **periodic Telegram updates every 12 hours**!

---

## 🎯 What's Configured

✅ **Periodic Updates**: Every 12 hours  
✅ **Telegram Notifications**: Working  
✅ **Email Notifications**: Need Gmail App Password  
✅ **Continuous Running**: Yes - bot runs 24/7  
✅ **Dry Run Mode**: Enabled (safe testing)  
✅ **Testnet**: Enabled (fake money)

---

## 🚀 Start the Bot

```bash
python3 main.py
```

The bot will:

- ✅ Test notifications at startup
- 📊 Monitor BNB price every 5 seconds
- 📅 Send status updates every 12 hours
- 💰 Execute trades automatically

---

## 📱 Telegram Status Updates

The bot sends detailed updates every 12 hours including:

- Current price & balance
- Profit/loss percentage
- Target & stop-loss levels
- Bot uptime & status

**To get updates**: Make sure you've started a conversation with @Binancecyptobot on Telegram!

---

## ⚙️ Customize Update Interval

Edit `.env` file:

```bash
UPDATE_INTERVAL_HOURS=6   # Change to any number of hours
```

Examples:

- `UPDATE_INTERVAL_HOURS=6` - Every 6 hours
- `UPDATE_INTERVAL_HOURS=24` - Daily
- `UPDATE_INTERVAL_HOURS=1` - Hourly

---

## 📧 Enable Email (Optional)

1. Go to: https://myaccount.google.com/apppasswords
2. Generate App Password for "Mail"
3. Replace `EMAIL_PASSWORD` in `.env` with 16-character password

---

## 🧪 Test Features

```bash
# Test Telegram connection
python3 test_telegram.py

# Test periodic updates
python3 test_periodic.py

# Get your Telegram chat ID
python3 get_my_chat_id.py
```

---

## 📈 Bot Strategy

- **Profit Target**: +0.5% (harvests profit)
- **Stop Loss**: -10% (sells all)
- **Monitor Interval**: Every 5 seconds
- **Running Mode**: Continuous 24/7

---

Your bot is ready! Start it and let it run continuously. You'll get updates every 12 hours! 🚀
