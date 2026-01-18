import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import random

# Constants
SYMBOL = "EURUSD"
LOT = 0.01
SLIPPAGE = 10
STOP_LOSS = 50
TAKE_PROFIT = 50
EPISODES = 1000

# RL setup
ACTIONS = ["HOLD", "BUY", "SELL"]
Q_table = {}  # Simple Q-table

# Initialize MT5
mt5.initialize()
account_info = mt5.account_info()
if account_info is None:
    print("Failed to connect to MT5!")
    mt5.shutdown()
    exit()
print(f"✅ Connected to account: {account_info.login}")

# Get price state (moving average delta)
def get_state(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
    df = pd.DataFrame(rates)
    if len(df) < 5:
        return "NO_DATA"
    ma_short = df['close'].tail(3).mean()
    ma_long = df['close'].tail(10).mean()
    delta = round(ma_short - ma_long, 5)
    return str(delta)

# Execute trade
def execute_trade(action):
    price = mt5.symbol_info_tick(SYMBOL).ask if action == "BUY" else mt5.symbol_info_tick(SYMBOL).bid
    order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": order_type,
        "price": price,
        "sl": price - STOP_LOSS * 0.0001 if action == "BUY" else price + STOP_LOSS * 0.0001,
        "tp": price + TAKE_PROFIT * 0.0001 if action == "BUY" else price - TAKE_PROFIT * 0.0001,
        "deviation": SLIPPAGE,
        "magic": 234000,
        "comment": "RL bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    return result

# Train the agent
def train_agent(episodes=EPISODES):
    for episode in range(episodes):
        state = get_state(SYMBOL)
        if state == "NO_DATA":
            print("⏳ Waiting for data...")
            time.sleep(5)
            continue

        if state not in Q_table:
            Q_table[state] = np.zeros(len(ACTIONS))  # Initialize Q-values

        action_idx = np.argmax(Q_table[state]) if random.random() > 0.1 else random.randint(0, 2)
        action = ACTIONS[action_idx]

        if action != "HOLD":
            result = execute_trade(action)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                reward = 1  # reward success
                print(f"📈 {action} Executed | Reward: {reward}")
            else:
                reward = -1  # punishment on fail
                print(f"⚠️ {action} Failed | Reward: {reward}")
        else:
            reward = 0
            print("🤖 Hold: No action taken.")

        # Update Q-value
        old_value = Q_table[state][action_idx]
        Q_table[state][action_idx] = old_value + 0.1 * (reward - old_value)

        time.sleep(5)

# Run the bot
try:
    print("🚀 RL HFT Bot Started...")
    train_agent()
finally:
    print("🔌 MT5 Shutdown...")
    mt5.shutdown()
    print("👋 Goodbye!")