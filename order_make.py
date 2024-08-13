import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
# from common import login,password,server
import numpy as np
import time
import schedule
import pandas_ta as ta
import talib as ta1
# import datetime
import pytz

login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)

symbol = 'GBPAUD.a'
VOLUME = 0.05
DEVIATION = 10
sl = None # Example stop loss
tp = 1.960421 # Example take profit


def market_order(symbol,volume,order_type,deviation,magic,stoploss,takeprofit):
    order_type_dict={
            'buy':mt.ORDER_TYPE_BUY,
            'sell': mt.ORDER_TYPE_SELL
        }

    price_dict={
        'buy':mt.symbol_info_tick(symbol).ask,
        'sell':mt.symbol_info_tick(symbol).bid
    }

    request={
        "action":mt.TRADE_ACTION_DEAL,
        "symbol":symbol,
        "volume":volume,
        "type":order_type_dict[order_type],
        "price":price_dict[order_type],
        "deviation":deviation,
        "magic":magic,
        # 'sl':stoploss,
        # 'tp':takeprofit,
        "deviation":deviation,
        "comment":"python market order",
        "type_time":mt.ORDER_TIME_GTC,
        "type_filling":mt.ORDER_FILLING_IOC,
    }
        # Conditionally add stop loss and take profit
    if stoploss is not None:
        request['sl'] = stoploss
    if takeprofit is not None:
        request['tp'] = takeprofit
        
    print("Sending order:", request)
    order_result = mt.order_send(request)
    
    # if order_result.retcode != mt.TRADE_RETCODE_DONE:
    #     print(f"Order failed, retcode={order_result.retcode}")
    # else:
    #     print("Order successful:", order_result)

    return order_result

a=market_order(symbol,VOLUME,'buy',DEVIATION,170,sl,tp)
print(a)