from datetime import datetime
import MetaTrader5 as mt5
import time

# === Config ===
SYMBOL = "EURUSD"
LOT_SIZE = 0.01
PIP_SIZE = 0.0001
# PIP_THRESHOLD = 2 * PIP_SIZE  # Trade when price moves by 2 pips   // old
PIP_THRESHOLD = 0.5 * PIP_SIZE  # Now trigger at 0.5 pip = 0.00005
SPREAD_LIMIT = 20  # Max spread in points (2 pips)
STOP_LOSS_PIPS = 5
TAKE_PROFIT_PIPS = 10
CHECK_INTERVAL = 1  # Seconds between price checks

# === Initialize ===
if not mt5.initialize():
    print("❌ Initialization failed:", mt5.last_error())
    quit()

if not mt5.symbol_select(SYMBOL, True):
    print(f"❌ Failed to select symbol {SYMBOL}")
    mt5.shutdown()
    quit()

print("🚀 HFT Bot Started...")

# === Get Initial Price ===
tick = mt5.symbol_info_tick(SYMBOL)
if tick is None:
    print("❌ Failed to get initial tick")
    mt5.shutdown()
    quit()

previous_price = tick.ask

# === Helper: Place Order ===
def place_order(order_type):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        print("⚠️ Tick data missing during order send.")
        return

    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    sl = price - STOP_LOSS_PIPS * PIP_SIZE if order_type == mt5.ORDER_TYPE_BUY else price + STOP_LOSS_PIPS * PIP_SIZE
    tp = price + TAKE_PROFIT_PIPS * PIP_SIZE if order_type == mt5.ORDER_TYPE_BUY else price - TAKE_PROFIT_PIPS * PIP_SIZE

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDJPY",
        "volume": 0.01,
        "type": order_type,
        "price": price,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "deviation": 10,
        "magic": 123456,
        "comment": "HFT Python Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    print(f"🛠️ Sending Order at {datetime.now()} | Price: {price}")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Order Failed: {result.comment}")
    else:
        print(f"✅ Order Placed: {result}")

# === Main Loop ===
try:
    while True:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            print("⚠️ Tick data not received.")
            time.sleep(CHECK_INTERVAL)
            continue

        current_ask = tick.ask
        current_bid = tick.bid
        spread = (current_ask - current_bid) / PIP_SIZE
        price_diff = current_ask - previous_price

        print(f"\n🕐 Tick Time: {datetime.now()}")
        print(f"Ask: {current_ask:.5f} | Bid: {current_bid:.5f}")
        print(f"Spread: {spread:.1f} pips | Price Diff: {price_diff:.5f}")

        if spread > SPREAD_LIMIT:
            print(f"⛔ High Spread ({spread:.1f} pips) – skipping.")
        elif abs(price_diff) >= PIP_THRESHOLD:
            if price_diff > 0:
                print("📈 BUY Signal Triggered")
                place_order(mt5.ORDER_TYPE_BUY)
            else:
                print("📉 SELL Signal Triggered")
                place_order(mt5.ORDER_TYPE_SELL)

            previous_price = current_ask
        else:
            print("🔁 No trade. Waiting for next tick...")
        print(f"⏳==================================================")

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("🛑 Bot manually stopped.")

finally:
    mt5.shutdown()
    print("👋 Goodbye!")