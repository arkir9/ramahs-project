"""
Simple backtester for the Harvester strategy.
Usage: adjust params below or convert to argparse.
"""
import os
import csv
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
TESTNET = os.getenv("TESTNET", "true").lower() in ("1", "true", "yes")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
if TESTNET:
    client.API_URL = "https://testnet.binance.vision/api"

SYMBOL = os.getenv("SYMBOL", "BNBUSDT")
INTERVAL = "1m"
START = None  # e.g. "2025-01-01"
END = None

TARGET_PCT = float(os.getenv("TARGET_PCT", "0.005"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.10"))
MIN_NOTIONAL = float(os.getenv("MIN_NOTIONAL", "1.0"))
SLIPPAGE_PCT = 0.0002   # 0.02% slippage assumption
FEE_PCT = 0.001         # 0.1% taker fee

def get_klines(symbol, interval, start_str=None, end_str=None, limit=1000):
    return client.get_klines(symbol=symbol, interval=interval, startTime=None if not start_str else int(datetime.strptime(start_str, "%Y-%m-%d").timestamp()*1000), endTime=None if not end_str else int(datetime.strptime(end_str, "%Y-%m-%d").timestamp()*1000), limit=limit)

def run_sim(initial_qty=1.0):
    # simple simulation: holds qty of base asset. baseline = initial_qty * price0
    klines = get_klines(SYMBOL, INTERVAL, START, END, limit=1000)
    if not klines:
        print("No klines returned")
        return

    # use close prices
    close_prices = [float(k[4]) for k in klines]
    timestamps = [k[0] for k in klines]

    qty = initial_qty
    baseline = qty * close_prices[0]
    realized = 0.0
    trades = []

    for i, price in enumerate(close_prices):
        value = qty * price
        target = baseline * (1 + TARGET_PCT)
        stop = baseline * (1 - STOP_LOSS_PCT)

        if value <= stop and qty > 0:
            # sell all
            sell_qty = qty
            proceeds = sell_qty * price * (1 - SLIPPAGE_PCT)
            proceeds *= (1 - FEE_PCT)
            realized += proceeds - baseline
            trades.append(("STOP", timestamps[i], price, sell_qty, proceeds, realized))
            qty = 0
            break

        if value >= target and qty > 0:
            profit_value = value - baseline
            sell_qty = profit_value / price
            if sell_qty * price >= MIN_NOTIONAL and sell_qty > 0:
                proceeds = sell_qty * price * (1 - SLIPPAGE_PCT)
                proceeds *= (1 - FEE_PCT)
                realized += proceeds
                qty = qty - sell_qty
                baseline = qty * price
                trades.append(("HARVEST", timestamps[i], price, sell_qty, proceeds, realized))

    # report
    print("Initial qty:", initial_qty)
    print("Final qty:", qty)
    print("Realized P&L (USDT):", realized)
    if trades:
        print("Trades:")
        for t in trades:
            ttype, ts, p, q, proceeds, cum = t
            dt = datetime.utcfromtimestamp(ts/1000).strftime("%Y-%m-%d %H:%M")
            print(f"{dt} {ttype} price={p:.4f} qty={q:.6f} proceeds={proceeds:.2f} cum={cum:.2f}")

if __name__ == "__main__":
    run_sim(initial_qty=1.0)