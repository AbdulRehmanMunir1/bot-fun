from datetime import datetime
import MetaTrader5 as mt5
import time

# === Configurable Parameters ===
SYMBOL = "EURUSD"
LOT_SIZE = 0.01
PIP_SIZE = 0.0001
PIP_THRESHOLD = 2 * PIP_SIZE  # Trigger trade if price moves by 2 pips
SPREAD_LIMIT = 20  # Max allowed spread in points (e.g., 20 = 2 pips)
STOP_LOSS_PIPS = 5
TAKE_PROFIT_PIPS = 10
CHECK_INTERVAL = 1  # Seconds between checks

# === Initialize MT5 ===
if not mt5.initialize():
    print("❌ Initialization failed:", mt5.last_error())
    quit()

if not mt5.symbol_select(SYMBOL, True):
    print(f"❌ Failed to select symbol {SYMBOL}")
    mt5.shutdown()
    quit()

# === Function: Get Current Spread in Points ===
def get_spread():
    tick = mt5.symbol_info_tick(SYMBOL)
    return (tick.ask - tick.bid) / PIP_SIZE

# === Function: Place Market Order with SL/TP ===
def place_order(order_type):
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    sl = price - STOP_LOSS_PIPS * PIP_SIZE if order_type == mt5.ORDER_TYPE_BUY else price + STOP_LOSS_PIPS * PIP_SIZE
    tp = price + TAKE_PROFIT_PIPS * PIP_SIZE if order_type == mt5.ORDER_TYPE_BUY else price - TAKE_PROFIT_PIPS * PIP_SIZE

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "deviation": 10,
        "magic": 123456,
        "comment": "HFT Bot SL/TP",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    print(f"{datetime.now()} - ✅ Order Sent: {result}")
    return result

# === Run Trading Loop ===
print("🚀 HFT Bot Started...")
previous_price = mt5.symbol_info_tick(SYMBOL).ask

try:
    while True:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            print("⚠️ Tick not received.")
            time.sleep(CHECK_INTERVAL)
            continue

        current_price = tick.ask
        spread = get_spread()

        if spread > SPREAD_LIMIT:
            print(f"⛔ High Spread ({spread:.1f}) – skipping trade.")
            time.sleep(CHECK_INTERVAL)
            continue

        price_diff = current_price - previous_price

        if abs(price_diff) >= PIP_THRESHOLD:
            if price_diff > 0:
                print(f"📈 BUY Signal | +{price_diff:.5f} | Spread: {spread:.1f}")
                place_order(mt5.ORDER_TYPE_BUY)
            else:
                print(f"📉 SELL Signal | {price_diff:.5f} | Spread: {spread:.1f}")
                place_order(mt5.ORDER_TYPE_SELL)

            previous_price = current_price

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("🛑 Bot manually stopped.")

finally:
    mt5.shutdown()
