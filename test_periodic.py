#!/usr/bin/env python3
"""
Test script for periodic Telegram updates
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_periodic_updates():
    """Test periodic updates with a short interval for demonstration."""

    print("🤖 Testing Periodic Updates")
    print("=" * 40)

    # Import bot functions
    from main import send_periodic_update, PERIODIC_UPDATES, UPDATE_INTERVAL_HOURS

    if not PERIODIC_UPDATES:
        print("❌ Periodic updates are disabled in .env")
        print("Set PERIODIC_UPDATES=true to enable")
        return

    print(f"✅ Periodic updates enabled: Every {UPDATE_INTERVAL_HOURS} hours")

    # Test data
    current_price = 1113.50
    current_value = 1113.50
    baseline_value = 1000.00
    cumulative_profit = 50.00
    balance_bnb = 1.0
    uptime_hours = 12.5

    print(f"\n📊 Test Data:")
    print(f"Price: ${current_price}")
    print(f"Value: ${current_value}")
    print(f"Baseline: ${baseline_value}")
    print(f"Profit: ${cumulative_profit}")
    print(f"Uptime: {uptime_hours} hours")

    print(f"\n📤 Sending test periodic update...")

    # Send test update
    send_periodic_update(
        current_price,
        current_value,
        baseline_value,
        cumulative_profit,
        balance_bnb,
        uptime_hours,
    )

    print("✅ Test periodic update sent!")

    print(f"\n📋 Configuration:")
    print(f"PERIODIC_UPDATES: {PERIODIC_UPDATES}")
    print(f"UPDATE_INTERVAL_HOURS: {UPDATE_INTERVAL_HOURS}")

    print(f"\n💡 To customize:")
    print(f"Add to .env file:")
    print(f"PERIODIC_UPDATES=true")
    print(f"UPDATE_INTERVAL_HOURS=12  # Change to any number of hours")


if __name__ == "__main__":
    test_periodic_updates()
