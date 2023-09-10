import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
from datetime import datetime

mt.initialize()

login=51339268
password='UZcMdrwV'
server='ICMarkets-Demo'

mt.login(login,password,server)

account_info=mt.account_info()
print(account_info)

balance=account_info.balance
equity=account_info.equity
print(balance,equity)

num_symbols=mt.symbols_total()
num_symbols

symbols=mt.symbols_get()
symbols

symbols_info=mt.symbol_info("AUDUSD")._asdict()
symbols_info

#get current symbol price
symbol_price=mt.symbol_info_tick("AUDUSD")._asdict()
symbol_price

#get history data
ohic_data=pd.DataFrame(mt.copy_rates_range("AUDUSD",mt.TIMEFRAME_D1,datetime(2023,1,1),datetime.now()))
ohic_data['time']=pd.to_datetime(ohic_data['time'],unit='s')
print(ohic_data)
fig=px.line(ohic_data,x=ohic_data['time'],y=ohic_data['close'])
fig.show()

#requesting tick data
tick_data=pd.DataFrame(mt.copy_ticks_range('EURUSD',datetime(2021,10,4),datetime.now(),mt.COPY_TICKS_ALL))
print(tick_data)
fig=px.line(tick_data,x=tick_data['time'],y=[tick_data['bid'],tick_data['ask']])
fig.show()

#total_number of order
num_orders=mt.orders_total()
print(num_orders)

#list of orders
orders=mt.orders_get()
print(orders)

#total_number of position
num_position=mt.positions_total()
num_position

#detail of position
positions=mt.positions_get()
positions

#number of history orders
num_order_history=mt.history_orders_total(datetime(2023,1,1),datetime(2023,8,19))
num_order_history
print(num_order_history)

#list history orders
order_history=mt.history_orders_get(datetime(2023,1,1),datetime(2023,8,25))
order_history

#number of history deals
num_deal_history=mt.history_deals_total(datetime(2023,1,1),datetime(2023,8,25))
num_deal_history

#list of history deals
deal_history=mt.history_deals_get(datetime(2023,1,1),datetime(2023,8,25))
deal_history

#send order to the market
request={
    "action": mt.TRADE_ACTION_DEAL,
    "symbol": "AUDUSD",
    "volume": 0.1,
    "type": mt.ORDER_TYPE_SELL,
    "price": mt.symbol_info_tick("AUDUSD").ask,
    "sl":0.0,
    "tp":0.0,
    "deviation":20,
    "magic":234000,
    "comment":"python script open",
    "type_time": mt.ORDER_TIME_GTC,
    "type_filling": mt.ORDER_FILLING_IOC,
}
order=mt.order_send(request)
print(order)

#close order to the market
request={
    "action": mt.TRADE_ACTION_DEAL,
    "symbol": "AUDUSD",
    "volume": 0.1,
    "type": mt.ORDER_TYPE_BUY,
    "position":466048246,
    "price": mt.symbol_info_tick("AUDUSD").ask,
    "sl":0.0,
    "tp":0.0,
    "deviation":20,
    "magic":234000,
    "comment":"python script open",
    "type_time": mt.ORDER_TIME_GTC,
    "type_filling": mt.ORDER_FILLING_IOC,
}
order=mt.order_send(request)
print(order)

