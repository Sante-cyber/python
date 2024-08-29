import MetaTrader5 as mt
import pandas as pd
from datetime import datetime, timedelta
from common import login,password,server

if mt.initialize():
    print('connect to MetaTrader5')
    mt.login(login,password,server)
    # mt.login(login,password,server)
    
    
    
def get_historical_data(symbol, timeframe, num_days):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_days)
    if rates is None:
        return None
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    return data

def get_20_day_low(data):
    return data['low'].rolling(window=20).min().iloc[-1]

def get_20_day_high(data):
    return data['high'].rolling(window=20).max().iloc[-1]
    

def turtle_soup_strategy(symbol):
    data = get_historical_data(symbol, timeframe, 25)
    if data is None or len(data) < 20:
        return None

    # Check if 20-day low was broken
    low_20_day = get_20_day_low(data[:-1])
    last_day = data.iloc[-1]

    # Ensure 3 days have passed since last 20-day low
    last_20_day_low_date = data[data['low'] == low_20_day].index[-1]
    if (last_day.name - last_20_day_low_date).days < 3:
        return None

    # Check if today's price breaks the 20-day low
    if last_day['low'] < low_20_day:
        # Set a pending buy order 5-10 points above the broken low
        entry_price = low_20_day + 0.0005  # 5 points above the 20-day low
        stop_loss = last_day['low'] - 0.0001  # 1 point below today's low

        return {
            "action": "Buy",
            "entry_price": entry_price,
            "stop_loss": stop_loss
        }
    return None


def place_order(symbol, action, entry_price, stop_loss):
    lot = 0.1  # Define your lot size
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY_LIMIT if action == "Buy" else mt5.ORDER_TYPE_SELL_LIMIT,
        "price": entry_price,
        "sl": stop_loss,
        "deviation": 10,
        "magic": 234000,
        "comment": "Turtle Soup trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    return result

def manage_trade(symbol, stop_loss):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        position = positions[0]
        current_price = mt5.symbol_info_tick(symbol).bid
        # Adjust StopLoss using Trailing Stop logic
        if current_price > position.price_open + 0.001:  # Example of trailing stop condition
            new_stop_loss = max(stop_loss, current_price - 0.0005)
            mt5.order_modify(position.ticket, sl=new_stop_loss)

def main():
    strategy_result = turtle_soup_strategy(symbol)
    if strategy_result:
        result = place_order(symbol, strategy_result['action'], strategy_result['entry_price'], strategy_result['stop_loss'])
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Order placed: {strategy_result}")
        else:
            print(f"Failed to place order: {result.comment}")
    else:
        print("No trade signal generated.")

    manage_trade(symbol, strategy_result['stop_loss'] if strategy_result else None)

if __name__ == "__main__":
    main()
    mt5.shutdown()
