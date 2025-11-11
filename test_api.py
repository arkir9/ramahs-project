#!/usr/bin/env python3
"""
Test Binance API connection
"""

import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
testnet = os.getenv("TESTNET", "true").lower() in ("1", "true", "yes")

print("🔍 Testing Binance API Connection")
print("=" * 50)

client = Client(api_key, api_secret)
if testnet:
    client.API_URL = "https://testnet.binance.vision/api"
    print(f"🌐 Network: TESTNET")
else:
    print(f"🌐 Network: MAINNET")

print(f"🔑 API Key: {api_key[:10]}...")
print()

# Test 1: Public data
try:
    print("1. Testing public price data...")
    ticker = client.get_symbol_ticker(symbol="BNBUSDT")
    print(f'   ✅ BNB Price: ${ticker["price"]}')
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Account info
try:
    print("2. Testing account access...")
    account = client.get_account()
    print(f"   ✅ Account connected successfully!")
    print(f'   Account type: {account.get("accountType", "N/A")}')
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Balance check
try:
    print("3. Testing balance check...")
    balance = client.get_asset_balance(asset="BNB")
    if balance:
        print(f'   ✅ BNB Balance: {balance.get("free", "0")} BNB')
        print(f'   Locked: {balance.get("locked", "0")} BNB')
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: All balances
try:
    print("4. Testing all balances...")
    account = client.get_account()
    balances = account.get("balances", [])
    non_zero = [b for b in balances if float(b.get("free", 0)) > 0]
    print(f"   ✅ Found {len(non_zero)} non-zero balances")
    for bal in non_zero[:5]:  # Show first 5
        print(f'      {bal["asset"]}: {bal["free"]}')
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 50)
print("\n💡 Tips:")
print("If you see -2015 errors:")
print("  1. Check IP whitelist in Binance API settings")
print('  2. Verify API key has "Spot & Margin Trading" permission')
print("  3. Make sure API key is enabled (not restricted)")
print("\n🧪 Run this test again after fixing API settings:")
print("   python3 test_api.py")
