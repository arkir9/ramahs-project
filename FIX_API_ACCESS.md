# 🔧 Fix Binance API Access Error (-2015)

## ❌ Current Issue

The error `APIError(code=-2015): Invalid API-key, IP, or permissions for action` means your API key can't access account data.

---

## ✅ Quick Fix (Choose One)

### Option 1: Add Your IP to Whitelist (Recommended for Security)

1. **Get your IP**: `41.90.172.137`
2. **Go to Binance** → API Management
3. **Edit your API key**
4. Under **"IP Access Restriction"**:
   - Select "Restrict access to trusted IPs only"
   - Click "Add IP"
   - Enter: `41.90.172.137`
   - Save

### Option 2: Disable IP Restriction (Easier, Less Secure)

1. **Go to Binance** → API Management
2. **Edit your API key**
3. Under **"IP Access Restriction"**:
   - Select **"Unrestricted"**
   - Save

---

## ✅ Verify API Permissions

Make sure these are **enabled**:

- ✅ **Enable Reading**
- ✅ **Enable Spot & Margin Trading** ← This is required!

If you just added trading permissions, it may take a few minutes to activate.

---

## 🧪 Test After Fixing

```bash
python3 test_api.py
```

You should see:

- ✅ Account connected successfully!
- ✅ BNB Balance: X BNB

---

## 📝 Summary

**Your IP**: `41.90.172.137`

**Action**: Add this IP to your Binance API whitelist OR set to "Unrestricted"

**Then test**: `python3 test_api.py`

Once this works, your bot will be able to:

- ✅ Check your BNB balance
- ✅ Execute trades automatically
- ✅ Send periodic updates
- ✅ Run continuously 24/7

---

## 🚀 Next Steps

After fixing the API access:

1. Test API: `python3 test_api.py`
2. Start bot: `python3 main.py`
3. Bot will send you Telegram updates every 12 hours!

🎉 Your bot is ready - just needs API whitelisting!
