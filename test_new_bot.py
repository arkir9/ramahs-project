import time
import math
import os
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()
SYMBOL = os.getenv("SYMBOL", "BNBUSDT")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))
TARGET_PCT = Decimal(os.getenv("TARGET_PCT", "0.005"))  # 0.5%
STOP_LOSS_PCT = Decimal(os.getenv("STOP_LOSS_PCT", "0.10"))  # 10% portfolio stop loss
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
QUANTITY_DECIMALS = int(os.getenv("QUANTITY_DECIMALS", "6"))
MIN_NOTIONAL = Decimal(os.getenv("MIN_NOTIONAL", "1.0"))

# ATR & Reentry Config
ATR_PERIOD = 14
ATR_MULTIPLIER = Decimal("1.5")
REENTRY_ATR_MULTIPLIER = Decimal("1.0")
REENTRY_STRATEGY = os.getenv("REENTRY_STRATEGY", "fixed_fraction")  # Options: fixed_fraction or limit_ladder
REENTRY_FRACTION = Decimal(os.getenv("REENTRY_FRACTION", "0.5"))  # Fraction of proceeds to use in reentry
LADDER_ORDERS = int(os.getenv("LADDER_ORDERS", "5"))
LADDER_SPACING_MULTIPLIER = Decimal(os.getenv("LADDER_SPACING_MULTIPLIER", "0.15"))
# -------------------------------

# Helper log function
def log(msg):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")

# Convert float or Decimal to Binance compatible quantity string
def floor_decimal(qty, decimals):
    d = Decimal(qty)
    rounded = d.quantize(Decimal(f'1e-{decimals}'), rounding=ROUND_DOWN)
    return rounded

# Binance API wrapper with retries
def with_retries(fn, *args, max_retries=3, backoff_sec=1.0, **kwargs):
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

# Fetch price
def fetch_price(client, symbol):
    tick = with_retries(client.get_symbol_ticker, symbol=symbol)
    return Decimal(tick["price"])

# Fetch balance
def fetch_balance(client, asset):
    bal = with_retries(client.get_asset_balance, asset=asset)
    return Decimal(bal.get("free", 0.0))

# Place market sell
def place_market_sell(client, symbol, quantity):
    if DRY_RUN:
        log(f"DRY RUN sell qty:{quantity} {symbol}")
        return None
    try:
        return with_retries(client.order_market_sell, symbol=symbol, quantity=str(quantity))
    except (BinanceAPIException, BinanceOrderException) as e:
        log(f"Order sell error: {e}")
        raise

# Place market buy by quote quantity (for re-entry)
def place_market_buy_quote(client, symbol, quote_qty):
    if DRY_RUN:
        log(f"DRY RUN buy quote qty:{quote_qty} {symbol}")
        return None
    try:
        return with_retries(client.order_market_buy, symbol=symbol, quoteOrderQty=str(quote_qty))
    except (BinanceAPIException, BinanceOrderException) as e:
        log(f"Order buy error: {e}")
        raise

# Calculate ATR (Average True Range)
def calculate_atr(client, symbol, period=ATR_PERIOD):
    klines = with_retries(client.get_klines, symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=period+1)
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
    atr = sum(trs) / Decimal(len(trs))
    return atr

def send_telegram(message):
    # Placeholder for your Telegram notification
    log(f"Telegram: {message}")

def main():
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    
    # Sync time with Binance to avoid signature errors
    try:
        server_time = with_retries(client.get_server_time)
        Client.TIME_OFFSET = server_time["serverTime"] - int(time.time() * 1000)
        client.RECVWINDOW = 5000
        log(f"Synced time offset: {Client.TIME_OFFSET} ms, recvWindow={client.RECVWINDOW}")
    except Exception as e:
        log(f"Time sync warning: {e}")
    
    base_asset = SYMBOL[:-4]  # Simple parsing BNB from BNBUSDT
    quote_asset = SYMBOL[-4:]  # USDT

    price = fetch_price(client, SYMBOL)
    balance_base = fetch_balance(client, base_asset)
    if balance_base <= 0:
        log(f"No {base_asset} balance to trade.")
        return

    baseline_value = balance_base * price
    cumulative_realized = Decimal("0")
    entry_price = price
    atr = calculate_atr(client, SYMBOL)
    stop_loss_price = entry_price - (ATR_MULTIPLIER * atr)
    reentry_price = entry_price - (REENTRY_ATR_MULTIPLIER * atr)
    last_atr_refresh = time.time()

    log(f"Started bot with price {price}, baseline {baseline_value}, ATR {atr}, stop loss {stop_loss_price}")

    try:
        while True:
            now = time.time()
            price = fetch_price(client, SYMBOL)
            balance_base = fetch_balance(client, base_asset)
            current_value = balance_base * price
            target_value = baseline_value * (Decimal("1") + TARGET_PCT)
            portfolio_stop_loss_value = baseline_value * (Decimal("1") - STOP_LOSS_PCT)

            if now - last_atr_refresh > 60 * 5:
                try:
                    atr = calculate_atr(client, SYMBOL)
                    last_atr_refresh = now
                    log(f"ATR refreshed to {atr}")
                except Exception as e:
                    log(f"Failed to refresh ATR: {e}")

            # Trailing stop loss updates
            new_stop = price - (ATR_MULTIPLIER * atr)
            if new_stop > stop_loss_price:
                stop_loss_price = new_stop

            log(f"Price {price}, Value {current_value}, Baseline {baseline_value}, Stop loss {stop_loss_price}")

            # ATR trailing stop loss triggered
            if price <= stop_loss_price and balance_base > 0:
                sell_qty = floor_decimal(balance_base, QUANTITY_DECIMALS)
                proceeds = sell_qty * price
                realized_pl = proceeds - baseline_value
                cumulative_realized += realized_pl
                send_telegram(f"ATR stop loss sell {sell_qty} {base_asset} at {price}, realized P&L {realized_pl}")
                place_market_sell(client, SYMBOL, sell_qty)
                # Prepare re-entry
                entry_price = price
                reentry_price = entry_price - (REENTRY_ATR_MULTIPLIER * atr)
                baseline_value = Decimal("0")
                log("Stopped after ATR stop loss")
                break 

            # Portfolio-wide stop loss triggered
            if current_value <= portfolio_stop_loss_value and balance_base > 0:
                sell_qty = floor_decimal(balance_base, QUANTITY_DECIMALS)
                proceeds = sell_qty * price
                realized_pl = proceeds - baseline_value
                cumulative_realized += realized_pl
                send_telegram(f"Portfolio stop loss sell {sell_qty} at {price}, loss {realized_pl}")
                place_market_sell(client, SYMBOL, sell_qty)
                entry_price = price
                reentry_price = entry_price - (REENTRY_ATR_MULTIPLIER * atr)
                baseline_value = Decimal("0")
                log("Stopped after portfolio stop loss")
                break

            # Profit harvesting with dynamic target tied to ATR
            atr_pct = (ATR_MULTIPLIER * atr) / price
            dynamic_target = max(TARGET_PCT, atr_pct / Decimal("2"))
            effective_target_value = baseline_value * (Decimal("1") + dynamic_target)

            if current_value >= effective_target_value and balance_base > 0:
                profit_value = current_value - baseline_value
                sell_amount_base = profit_value / price
                sell_amount_base = floor_decimal(sell_amount_base, QUANTITY_DECIMALS)
                if sell_amount_base * price < MIN_NOTIONAL:
                    log("Profit sell amount below min notional, skipping")
                    time.sleep(CHECK_INTERVAL)
                    continue
                proceeds = sell_amount_base * price
                realized_pl = proceeds - (sell_amount_base * entry_price)
                cumulative_realized += realized_pl
                send_telegram(f"Profit harvesting sell {sell_amount_base} at {price}, realized {realized_pl}")
                place_market_sell(client, SYMBOL, sell_amount_base)
                time.sleep(1)
                new_balance = fetch_balance(client, base_asset)
                baseline_value = new_balance * price
                entry_price = price
                stop_loss_price = entry_price - (ATR_MULTIPLIER * atr)
                reentry_price = entry_price - (REENTRY_ATR_MULTIPLIER * atr)
                log(f"Harvest done, baseline {baseline_value}, cumulative realized {cumulative_realized}")

                # Configurable re-entry strategy
                if price <= reentry_price:
                    if REENTRY_STRATEGY == "fixed_fraction":
                        buy_quote_qty = floor_decimal(proceeds * REENTRY_FRACTION, QUANTITY_DECIMALS)
                        if buy_quote_qty * Decimal("1") >= MIN_NOTIONAL:
                            log(f"Attempting fixed fraction re-entry buy quote {buy_quote_qty}")
                            if not DRY_RUN:
                                try:
                                    place_market_buy_quote(client, SYMBOL, buy_quote_qty)
                                    log("Re-entry fixed fraction buy executed")
                                except Exception as e:
                                    log(f"Re-entry buy failed: {e}")
                    elif REENTRY_STRATEGY == "limit_ladder":
                        base_qty = ((proceeds * REENTRY_FRACTION) / LADDER_ORDERS)
                        for i in range(1, LADDER_ORDERS + 1):
                            limit_price = entry_price - (LADDER_SPACING_MULTIPLIER * Decimal(i) * atr)
                            buy_qty = floor_decimal(base_qty / limit_price, QUANTITY_DECIMALS)
                            if buy_qty * limit_price >= MIN_NOTIONAL:
                                log(f"Placing limit ladder buy order {buy_qty} at {limit_price}")
                                if not DRY_RUN:
                                    try:
                                        client.create_order(
                                            symbol=SYMBOL,
                                            side="BUY",
                                            type="LIMIT",
                                            timeInForce="GTC",
                                            quantity=str(float(buy_qty)),
                                            price=str(float(limit_price)),
                                        )
                                        log(f"Ladder buy order placed: qty {buy_qty} @ {limit_price}")
                                    except Exception as e:
                                        log(f"Failed limit ladder order: {e}")

                continue

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("User stopped bot")
    except Exception as e:
        log(f"Error: {e}")
        send_telegram(f"Bot error: {e}")

if __name__ == "__main__":
    main()

