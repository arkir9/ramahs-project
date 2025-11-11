#!/usr/bin/env python3
"""
Test script to verify Telegram configuration and notifications
without modifying the main bot code.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def test_telegram():
    """Test Telegram bot configuration and send a test message."""
    
    print("=" * 60)
    print("Telegram Configuration Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Missing'}")
    print(f"   Chat ID: {'✅ Set' if TELEGRAM_CHAT_ID else '❌ Missing'}")
    print()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: Telegram configuration is incomplete!")
        print("   Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return False
    
    # Test bot token validity
    print("🔍 Testing Bot Token...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                bot_name = bot_info["result"].get("username", "Unknown")
                print(f"   ✅ Bot Token is valid")
                print(f"   Bot Username: @{bot_name}")
            else:
                print(f"   ❌ Bot Token is invalid: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Failed to verify bot token (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Error checking bot token: {e}")
        return False
    
    print()
    
    # Test sending message
    print("📤 Testing Message Send...")
    test_message = "🤖 BNB Bot Test\n\nThis is a test message to verify Telegram notifications are working correctly.\n\n✅ If you receive this, your Telegram configuration is working!"
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": test_message
        }
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("   ✅ Test message sent successfully!")
                print(f"   Message ID: {result['result'].get('message_id', 'N/A')}")
                print()
                print("✅ Telegram notifications are working correctly!")
                return True
            else:
                error_desc = result.get("description", "Unknown error")
                print(f"   ❌ Failed to send message: {error_desc}")
                
                # Common error messages
                if "chat not found" in error_desc.lower():
                    print("   💡 Tip: Make sure you've started a conversation with your bot first")
                elif "unauthorized" in error_desc.lower():
                    print("   💡 Tip: Check if your bot token is correct")
                return False
        else:
            print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out. Check your internet connection.")
        return False
    except Exception as e:
        print(f"   ❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    print()
    success = test_telegram()
    print()
    print("=" * 60)
    if success:
        print("✅ All Telegram tests passed!")
    else:
        print("❌ Telegram test failed. Please check your configuration.")
    print("=" * 60)
    print()
