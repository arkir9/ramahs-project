# -------------------------------------------
# BNB Profit Harvester Bot (Improved with ATR)
# -------------------------------------------
# Features:
# 1. ATR-based trailing stop loss
# 2. Dynamic profit targets based on volatility
# 3. Exchange filter validation
# 4. Telegram notifications for trades only
# 5. Re-entry strategies (optional)
# -------------------------------------------

import time
import math
import os
import requests
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timezone
from typing import Dict, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()
TESTNET = os.getenv("TESTNET", "false").lower() in ("1", "true", "yes")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SYMBOL = os.getenv("SYMBOL", "BNBUSDT")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))
TARGET_PCT = Decimal(os.getenv("TARGET_PCT", "0.005"))  # 0.5%
STOP_LOSS_PCT = Decimal(os.getenv("STOP_LOSS_PCT", "0.10"))  # 10% portfolio stop loss
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
QUANTITY_DECIMALS = int(os.getenv("QUANTITY_DECIMALS", "6"))
MIN_NOTIONAL = Decimal(os.getenv("MIN_NOTIONAL", "1.0"))

# ATR & Reentry Config
ATR_PERIOD = 14
ATR_MULTIPLIER = Decimal(os.getenv("ATR_MULTIPLIER", "1.5"))
USE_ATR_STOP_LOSS = os.getenv("USE_ATR_STOP_LOSS", "true").lower() in (
    "1",
    "true",
    "yes",
)
REENTRY_STRATEGY = os.getenv(
    "REENTRY_STRATEGY", "none"
)  # Options: none, fixed_fraction, limit_ladder
REENTRY_FRACTION = Decimal(os.getenv("REENTRY_FRACTION", "0.5"))
LADDER_ORDERS = int(os.getenv("LADDER_ORDERS", "5"))
LADDER_SPACING_MULTIPLIER = Decimal(os.getenv("LADDER_SPACING_MULTIPLIER", "0.15"))


# -------------------------
# NOTIFICATION FUNCTIONS
# -------------------------
def send_telegram(message):
    """Send alerts to Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM] {message}")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"[TELEGRAM] ✅ {message}")
            return True
        else:
            print(f"[TELEGRAM ERROR] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False


def log(msg):
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


# -------------------------
# BINANCE API HELPERS
# -------------------------
def with_retries(fn, *args, max_retries=3, backoff_sec=1.0, **kwargs):
    """Run API call with retries and backoff."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(backoff_sec * attempt)
            else:
                pass
    raise last_err


def fetch_symbol_info(client: Client, symbol: str) -> Dict[str, Any]:
    """Fetch symbol information including base/quote assets and filters."""
    info = with_retries(client.get_exchange_info)
    sym = next((s for s in info.get("symbols", []) if s.get("symbol") == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found in exchange info")

    result = {
        "baseAsset": sym.get("baseAsset"),
        "quoteAsset": sym.get("quoteAsset"),
        "stepSize": None,
        "minQty": None,
        "tickSize": None,
        "minNotional": None,
    }

    for f in sym.get("filters", []):
        ft = f.get("filterType")
        if ft == "LOT_SIZE":
            result["stepSize"] = Decimal(f.get("stepSize", "0.000001"))
            result["minQty"] = Decimal(f.get("minQty", "0.0"))
        elif ft == "PRICE_FILTER":
            result["tickSize"] = Decimal(f.get("tickSize", "0.01"))
        elif ft == "MIN_NOTIONAL":
            result["minNotional"] = Decimal(f.get("minNotional", "0.0"))
        elif ft == "NOTIONAL":
            result["minNotional"] = Decimal(f.get("minNotional", "0.0"))

    return result


def floor_decimal(qty: Decimal, step_size: Decimal) -> Decimal:
    """Round quantity down to nearest step size."""
    if qty <= 0 or step_size <= 0:
        return Decimal("0")
    steps = (qty / step_size).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return steps * step_size


def fetch_price(client, symbol):
    """Get latest price."""
    tick = with_retries(client.get_symbol_ticker, symbol=symbol)
    return Decimal(tick["price"])


def fetch_balance(client, asset):
    """Get free balance for asset."""
    bal = with_retries(client.get_asset_balance, asset=asset)
    return Decimal(bal.get("free", "0.0"))


def calculate_atr(client, symbol, period=ATR_PERIOD):
    """Calculate Average True Range."""
    try:
        klines = with_retries(
            client.get_klines,
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_5MINUTE,
            limit=period + 1,
        )

        if len(klines) < period + 1:
            raise ValueError(
                f"Insufficient kline data: got {len(klines)}, need {period + 1}"
            )

        highs = [Decimal(k[2]) for k in klines]
        lows = [Decimal(k[3]) for k in klines]
        closes = [Decimal(k[4]) for k in klines]

        trs = []
        for i in range(1, len(klines)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            trs.append(tr)

        if not trs:
            raise ValueError("No TR values calculated")

        atr = sum(trs) / Decimal(len(trs))
        return atr
    except Exception as e:
        log(f"ATR calculation error: {e}")
        raise


def place_market_sell(client, symbol, quantity: Decimal, step_size: Decimal):
    """Place market sell order."""
    qty_str = str(floor_decimal(quantity, step_size))
    if DRY_RUN:
        log(f"[DRY RUN] Market sell: {qty_str} {symbol}")
        return {"status": "DRY_RUN", "executedQty": qty_str}
    try:
        return with_retries(client.order_market_sell, symbol=symbol, quantity=qty_str)
    except (BinanceAPIException, BinanceOrderException) as e:
        log(f"Order sell error: {e}")
        send_telegram(f"❌ Sell order failed: {e}")
        raise


def place_market_buy_quote(client, symbol, quote_qty: Decimal):
    """Place market buy by quote quantity."""
    qty_str = str(quote_qty.quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    if DRY_RUN:
        log(f"[DRY RUN] Market buy quote: {qty_str} USDT {symbol}")
        return {"status": "DRY_RUN"}
    try:
        return with_retries(
            client.order_market_buy, symbol=symbol, quoteOrderQty=qty_str
        )
    except (BinanceAPIException, BinanceOrderException) as e:
        log(f"Order buy error: {e}")
        send_telegram(f"❌ Buy order failed: {e}")
        raise


# -------------------------
# MAIN BOT LOGIC
# -------------------------
def main():
    log("Starting BNB Profit Harvester Bot (Improved with ATR)...")

    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        log("ERROR: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")
        return

    if DRY_RUN:
        log("DRY_RUN=True. No real trades will be placed.")

    if TESTNET:
        log("Using Binance TESTNET")

    # Initialize client
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

    if TESTNET:
        client.API_URL = "https://testnet.binance.vision/api"

    # Sync time with Binance
    try:
        server_time = with_retries(client.get_server_time)
        Client.TIME_OFFSET = server_time["serverTime"] - int(time.time() * 1000)
        client.RECVWINDOW = 5000
        log(f"Synced time offset: {Client.TIME_OFFSET} ms")
    except Exception as e:
        log(f"Time sync warning: {e}")

    # Get symbol info
    try:
        symbol_info = fetch_symbol_info(client, SYMBOL)
        base_asset = symbol_info["baseAsset"]
        quote_asset = symbol_info["quoteAsset"]
        step_size = symbol_info["stepSize"] or Decimal(f"1e-{QUANTITY_DECIMALS}")
        min_notional = symbol_info["minNotional"] or MIN_NOTIONAL
        log(f"Symbol: {SYMBOL}, Base: {base_asset}, Quote: {quote_asset}")
        log(f"Step size: {step_size}, Min notional: {min_notional}")
    except Exception as e:
        log(f"ERROR: Failed to get symbol info: {e}")
        return

    # Get initial balance and price
    price = fetch_price(client, SYMBOL)
    balance_base = fetch_balance(client, base_asset)

    if balance_base <= 0:
        log(f"No {base_asset} balance to trade.")
        return

    # Initialize state
    baseline_value = balance_base * price
    cumulative_realized = Decimal("0")
    entry_price = price

    # Calculate ATR and set stop loss
    atr = None
    stop_loss_price = None
    use_atr_stop = USE_ATR_STOP_LOSS  # Local variable that can be modified
    if use_atr_stop:
        try:
            atr = calculate_atr(client, SYMBOL)
            stop_loss_price = entry_price - (ATR_MULTIPLIER * atr)
            log(f"ATR: {atr:.4f}, Initial stop loss: {stop_loss_price:.4f}")
        except Exception as e:
            log(f"Failed to calculate ATR: {e}. Disabling ATR stop loss.")
            use_atr_stop = False
            atr = None
            stop_loss_price = None

    last_atr_refresh = time.time()

    log(
        f"Started: Price {price:.4f}, Balance {balance_base:.6f} {base_asset}, Baseline {baseline_value:.2f} {quote_asset}"
    )

    try:
        while True:
            now = time.time()
            price = fetch_price(client, SYMBOL)
            balance_base = fetch_balance(client, base_asset)
            current_value = balance_base * price

            # Refresh ATR every 5 minutes
            if use_atr_stop and (now - last_atr_refresh > 60 * 5):
                try:
                    atr = calculate_atr(client, SYMBOL)
                    last_atr_refresh = now
                    log(f"ATR refreshed: {atr:.4f}")
                except Exception as e:
                    log(f"Failed to refresh ATR: {e}")

            # Update trailing stop loss
            if use_atr_stop and atr:
                new_stop = price - (ATR_MULTIPLIER * atr)
                if stop_loss_price is None or new_stop > stop_loss_price:
                    stop_loss_price = new_stop
                    log(f"Trailing stop updated: {stop_loss_price:.4f}")

            portfolio_stop_loss_value = baseline_value * (Decimal("1") - STOP_LOSS_PCT)

            log(
                f"Price: {price:.4f}, Value: {current_value:.2f}, Baseline: {baseline_value:.2f}"
            )
            if use_atr_stop and stop_loss_price:
                log(
                    f"ATR Stop: {stop_loss_price:.4f}, Portfolio Stop: {portfolio_stop_loss_value:.2f}"
                )

            # ATR trailing stop loss (if enabled)
            if (
                use_atr_stop
                and stop_loss_price
                and price <= stop_loss_price
                and balance_base > 0
            ):
                sell_qty = floor_decimal(balance_base, step_size)
                if sell_qty * price >= min_notional:
                    # Send notification BEFORE trade
                    msg_before = f"🛑 ATR Stop Loss Triggered\n\nAbout to sell {sell_qty:.6f} {base_asset} at ~{price:.2f} {quote_asset}\nPrice dropped below trailing stop: {stop_loss_price:.2f}"
                    send_telegram(msg_before)

                    # Execute trade
                    try:
                        order_result = place_market_sell(
                            client, SYMBOL, sell_qty, step_size
                        )
                        proceeds = sell_qty * price
                        realized_pl = proceeds - baseline_value
                        cumulative_realized += realized_pl

                        # Send confirmation AFTER trade
                        executed_qty = (
                            order_result.get("executedQty", str(sell_qty))
                            if order_result
                            else str(sell_qty)
                        )
                        msg_after = f"✅ ATR Stop Loss Executed\n\nSold {executed_qty} {base_asset} at {price:.2f} {quote_asset}\nP&L: {realized_pl:.2f} {quote_asset}\nTotal realized: {cumulative_realized:.2f} {quote_asset}"
                        send_telegram(msg_after)

                        log(
                            f"ATR stop loss executed. Cumulative P&L: {cumulative_realized:.2f}"
                        )
                    except Exception as e:
                        # Error notification already sent by place_market_sell
                        log(f"ATR stop loss trade failed: {e}")
                    break

            # Portfolio-wide stop loss
            if current_value <= portfolio_stop_loss_value and balance_base > 0:
                sell_qty = floor_decimal(balance_base, step_size)
                if sell_qty * price >= min_notional:
                    # Send notification BEFORE trade
                    loss_pct = ((current_value - baseline_value) / baseline_value) * 100
                    msg_before = f"🛑 Portfolio Stop Loss Triggered\n\nAbout to sell {sell_qty:.6f} {base_asset} at ~{price:.2f} {quote_asset}\nPortfolio dropped {loss_pct:.2f}% below baseline"
                    send_telegram(msg_before)

                    # Execute trade
                    try:
                        order_result = place_market_sell(
                            client, SYMBOL, sell_qty, step_size
                        )
                        proceeds = sell_qty * price
                        realized_pl = proceeds - baseline_value
                        cumulative_realized += realized_pl

                        # Send confirmation AFTER trade
                        executed_qty = (
                            order_result.get("executedQty", str(sell_qty))
                            if order_result
                            else str(sell_qty)
                        )
                        msg_after = f"✅ Portfolio Stop Loss Executed\n\nSold {executed_qty} {base_asset} at {price:.2f} {quote_asset}\nLoss: {realized_pl:.2f} {quote_asset}\nTotal realized: {cumulative_realized:.2f} {quote_asset}"
                        send_telegram(msg_after)

                        log(
                            f"Portfolio stop loss executed. Cumulative P&L: {cumulative_realized:.2f}"
                        )
                    except Exception as e:
                        # Error notification already sent by place_market_sell
                        log(f"Portfolio stop loss trade failed: {e}")
                    break

            # Profit harvesting
            target_value = baseline_value * (Decimal("1") + TARGET_PCT)

            # Use dynamic target if ATR is available
            if use_atr_stop and atr:
                atr_pct = (ATR_MULTIPLIER * atr) / price
                dynamic_target = max(TARGET_PCT, atr_pct / Decimal("2"))
                target_value = baseline_value * (Decimal("1") + dynamic_target)

            if current_value >= target_value and balance_base > 0:
                profit_value = current_value - baseline_value
                sell_amount_base = profit_value / price
                sell_amount_base = floor_decimal(sell_amount_base, step_size)

                if sell_amount_base <= 0 or sell_amount_base * price < min_notional:
                    log("Profit sell amount below min notional, skipping")
                    time.sleep(CHECK_INTERVAL)
                    continue

                profit_pct = (profit_value / baseline_value) * 100

                # Send notification BEFORE trade
                msg_before = f"💰 Profit Target Reached\n\nAbout to harvest profit:\n• Sell {sell_amount_base:.6f} {base_asset} at ~{price:.2f} {quote_asset}\n• Profit: {profit_pct:.2f}% ({profit_value:.2f} {quote_asset})"
                send_telegram(msg_before)

                # Execute trade
                try:
                    order_result = place_market_sell(
                        client, SYMBOL, sell_amount_base, step_size
                    )
                    proceeds = sell_amount_base * price
                    realized_pl = proceeds - (sell_amount_base * entry_price)
                    cumulative_realized += realized_pl

                    # Send confirmation AFTER trade
                    executed_qty = (
                        order_result.get("executedQty", str(sell_amount_base))
                        if order_result
                        else str(sell_amount_base)
                    )
                    actual_price = (
                        Decimal(order_result.get("price", str(price)))
                        if order_result and order_result.get("price")
                        else price
                    )
                    msg_after = f"✅ Profit Harvested\n\nSold {executed_qty} {base_asset} at {actual_price:.2f} {quote_asset}\nProfit: {realized_pl:.2f} {quote_asset}\nTotal realized: {cumulative_realized:.2f} {quote_asset}"
                    send_telegram(msg_after)

                    time.sleep(1)
                    new_balance = fetch_balance(client, base_asset)
                    baseline_value = new_balance * price
                    entry_price = price

                    # Update stop loss
                    if use_atr_stop and atr:
                        stop_loss_price = entry_price - (ATR_MULTIPLIER * atr)

                    log(
                        f"Harvest done. New baseline: {baseline_value:.2f}, Cumulative: {cumulative_realized:.2f}"
                    )

                    # Re-entry logic (if enabled and price dropped)
                    if REENTRY_STRATEGY != "none" and proceeds >= min_notional:
                        # Only re-enter if price dropped significantly (e.g., 2% below entry)
                        price_drop_threshold = entry_price * Decimal("0.98")

                        if price <= price_drop_threshold:
                            if REENTRY_STRATEGY == "fixed_fraction":
                                buy_quote_qty = floor_decimal(
                                    proceeds * REENTRY_FRACTION, Decimal("0.01")
                                )
                                if buy_quote_qty >= min_notional:
                                    # Send notification BEFORE re-entry
                                    drop_pct = (
                                        (entry_price - price) / entry_price
                                    ) * 100
                                    msg_before = f"🔄 Re-entry Opportunity\n\nPrice dropped {drop_pct:.2f}% after profit harvest\nAbout to buy {buy_quote_qty:.2f} {quote_asset} worth of {base_asset} at ~{price:.2f}"
                                    send_telegram(msg_before)

                                    # Execute re-entry
                                    try:
                                        order_result = place_market_buy_quote(
                                            client, SYMBOL, buy_quote_qty
                                        )
                                        time.sleep(1)
                                        new_balance = fetch_balance(client, base_asset)
                                        baseline_value = new_balance * price
                                        entry_price = price
                                        if use_atr_stop and atr:
                                            stop_loss_price = entry_price - (
                                                ATR_MULTIPLIER * atr
                                            )

                                        # Send confirmation AFTER re-entry
                                        msg_after = (
                                            f"✅ Re-entry Completed\n\nBought {new_balance:.6f} {base_asset} at {price:.2f} {quote_asset}\nNew baseline: {baseline_value:.2f} {quote_asset}\nNew stop loss: {stop_loss_price:.2f} {quote_asset}"
                                            if use_atr_stop and atr
                                            else f"✅ Re-entry Completed\n\nBought {new_balance:.6f} {base_asset} at {price:.2f} {quote_asset}\nNew baseline: {baseline_value:.2f} {quote_asset}"
                                        )
                                        send_telegram(msg_after)

                                        log(
                                            f"Re-entry completed. New baseline: {baseline_value:.2f}"
                                        )
                                    except Exception as e:
                                        # Error notification already sent by place_market_buy_quote
                                        log(f"Re-entry trade failed: {e}")
                            elif REENTRY_STRATEGY == "limit_ladder":
                                log(
                                    "Limit ladder re-entry not fully implemented (requires order tracking)"
                                )
                                # TODO: Implement limit ladder with order tracking

                except Exception as e:
                    # Error notification already sent by place_market_sell
                    log(f"Profit harvest trade failed: {e}")
                    time.sleep(CHECK_INTERVAL)
                    continue

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("Bot stopped by user")
    except Exception as e:
        log(f"Error: {e}")
        send_telegram(f"⚠️ Bot error: {e}")


if __name__ == "__main__":
    main()
