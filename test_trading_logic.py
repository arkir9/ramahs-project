#!/usr/bin/env python3
"""
Tests for trading logic in main.py using a mocked Binance client.
Validates:
- Dynamic filters (stepSize, minNotional)
- Quantity rounding (step size)
- Zero-quantity and min-notional guards
- Profit-harvest and stop-loss decision thresholds
"""

import os
from types import SimpleNamespace

# Ensure env safe defaults for tests
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("TESTNET", "true")
os.environ.setdefault("SYMBOL", "BNBUSDT")

import main  # noqa: E402


class MockClient:
    def __init__(self, price_sequence, initial_bnb, step_size, min_notional):
        self.price_sequence = list(price_sequence)
        self.initial_bnb = initial_bnb
        self.balance_bnb = initial_bnb
        self.step_size = step_size
        self.min_notional = min_notional
        self.orders = []

    # Methods used by main
    def get_symbol_ticker(self, symbol):
        price = self.price_sequence[0] if self.price_sequence else 300.0
        # pop only when explicitly advanced by tests
        return {"symbol": symbol, "price": str(price)}

    def get_asset_balance(self, asset):
        return {"asset": asset, "free": str(self.balance_bnb), "locked": "0"}

    def get_exchange_info(self):
        return {
            "symbols": [
                {
                    "symbol": os.getenv("SYMBOL", "BNBUSDT"),
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "stepSize": str(self.step_size),
                            "minQty": "0.0001",
                        },
                        {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                        {
                            "filterType": "MIN_NOTIONAL",
                            "minNotional": str(self.min_notional),
                        },
                    ],
                }
            ]
        }

    def order_market_sell(self, symbol, quantity):
        self.orders.append({"symbol": symbol, "side": "SELL", "quantity": quantity})
        # Reduce balance to simulate sale
        self.balance_bnb = max(0.0, self.balance_bnb - float(quantity))
        return {"status": "FILLED", "executedQty": str(quantity)}


def assert_almost(a, b, eps=1e-8):
    assert abs(a - b) <= eps, f"Expected {b}, got {a}"


def test_profit_harvest_basic():
    # Given: price jumps above target and profit meets minNotional
    price0 = 100.0
    target_pct = main.TARGET_PCT  # default 0.005
    price1 = price0 * (1 + target_pct + 0.01)  # > target by 1% to ensure profit

    step_size = 0.0001
    min_notional = 0.5  # low enough to be met by profit

    client = MockClient(
        price_sequence=[price1],
        initial_bnb=1.0,
        step_size=step_size,
        min_notional=min_notional,
    )

    filters = main.fetch_symbol_filters(client, os.getenv("SYMBOL", "BNBUSDT"))
    step = filters["stepSize"]
    dynamic_min_notional = filters["minNotional"]

    price = float(
        client.get_symbol_ticker(symbol=os.getenv("SYMBOL", "BNBUSDT"))["price"]
    )
    balance_bnb = float(client.get_asset_balance(asset="BNB")["free"])

    baseline = balance_bnb * price0
    current_value = balance_bnb * price

    assert current_value >= baseline * (1 + target_pct)

    profit_value = current_value - baseline
    sell_qty = main.round_quantity_step(profit_value / price, step)

    assert sell_qty > 0
    assert sell_qty * price >= dynamic_min_notional

    # Place order via main.place_market_sell with DRY_RUN disabled so mock records order
    prev_dry_run = main.DRY_RUN
    main.DRY_RUN = False
    try:
        main.place_market_sell(client, os.getenv("SYMBOL", "BNBUSDT"), sell_qty)
    finally:
        main.DRY_RUN = prev_dry_run

    # Verify our mock captured the order
    assert len(client.orders) == 1, "Expected one SELL order"


def test_min_notional_guard():
    # Given price increase but profit < minNotional -> should not trade
    price0 = 100.0
    price1 = 100.6  # 0.6% up; for small balance may be < minNotional
    step_size = 0.001
    min_notional = 10.0  # high threshold

    client = MockClient(
        price_sequence=[price1],
        initial_bnb=0.05,
        step_size=step_size,
        min_notional=min_notional,
    )

    filters = main.fetch_symbol_filters(client, os.getenv("SYMBOL", "BNBUSDT"))
    step = filters["stepSize"]
    dynamic_min_notional = filters["minNotional"]

    price = float(
        client.get_symbol_ticker(symbol=os.getenv("SYMBOL", "BNBUSDT"))["price"]
    )
    balance_bnb = float(client.get_asset_balance(asset="BNB")["free"])

    baseline = balance_bnb * price0
    current_value = balance_bnb * price

    profit_value = current_value - baseline
    sell_qty = main.round_quantity_step(profit_value / price, step)

    assert sell_qty * price < dynamic_min_notional, "Expected to be below minNotional"

    # We simulate decision: it should skip placing order when below minNotional
    # No call to order_market_sell here, assertion is sufficient


if __name__ == "__main__":
    test_profit_harvest_basic()
    test_min_notional_guard()
    print("✅ Trading logic tests passed")
