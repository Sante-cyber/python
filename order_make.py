symbol = 'GBPAUD.a'
volume = 0.01
order_type = mt.ORDER_TYPE_BUY
price = mt.symbol_info_tick(symbol).ask
deviation = 10
stop_loss = 1.8975510128919515  # Example stop loss
take_profit = 1.9204089871080487  # Example take profit

# Create an order request
request = {
    "action": mt.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": order_type,
    "price": price,
    "deviation": deviation,
    "magic": 170,  # Magic number should be an integer
    'sl': stop_loss,
    'tp': take_profit,
    "comment": "python market order",
    "type_time": mt.ORDER_TIME_GTC,
    "type_filling": mt.ORDER_FILLING_IOC,
}

# Send the order
order_result = mt.order_send(request)