import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
from datetime import datetime
from common import login,password,server
import time
import os
import sys

# os.environ['PYSPARK_PYTHON'] = sys.executable
# os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
# login=51339268
# password='UZcMdrwV'
# server='ICMarkets-Demo'

mt.initialize()

mt.login(login,password,server)

symbol='AUDUSD'
timeframe=mt.TIMEFRAME_M10
volume=0.01
strategy_name='ma_trendfollowing'

def get_sma(symbol,timeframe,period):
    sma=pd.DataFrame(mt.copy_rates_from_pos(symbol,timeframe,1,period))['close'].mean()
    return sma

def close_position(position,deviation=20,magic=12345):

    order_type_dict={
        0:mt.ORDER_TYPE_SELL,
        1:mt.ORDER_TYPE_BUY
    }

    price_dict={
        0: mt.symbol_info_tick(symbol).bid,
        1: mt.symbol_info_tick(symbol).ask
    }

    request={
        "action":mt.TRADE_ACTION_DEAL,
        "position":position['ticket'],
        "symbol":symbol,
        "volume":volume,
        "type":order_type_dict[position['type']],
        "price":price_dict[position['type']],
        "deviation":deviation,
        "comment":strategy_name,
        "type_time":mt.ORDER_TIME_GTC,
        "type_filling":mt.ORDER_FILLING_IOC,
    }

    order_result=mt.order_send(request)
    return(order_result)


def close_positions(order_type):
    order_type_dict={
        'buy':0,
        'sell':1
    }
    if mt.positions_total()>0:
        positions=mt.positions_get()
        positions_df=pd.DataFrame(positions,columns=positions[0]._asdict().keys())

        if order_type!='all':
            positions_df=positions_df[(positions_df['type']==order_type_dict[order_type])]

        for i,position in positions_df.iterrows():
            order_result=close_position(position)
            print('order_result',order_result)

def check_allowed_trading_hours():
    if 9<datetime.now().hour<17:
        return True
    else:
        return False

def market_order(symbol,volume,order_type,deviation=20,magic=12345):
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
        'sl':0.0,
        'tp':0.0,
        "deviation":deviation,
        "comment":strategy_name,
        "type_time":mt.ORDER_TIME_GTC,
        "type_filling":mt.ORDER_FILLING_IOC,
    }

    order_result=mt.order_send(request)
    return(order_result)

if __name__=='__main__':
    is_initialized=mt.initialize()
    print('initialize:',is_initialized)

    is_logged_in=mt.login(login,password,server)
    print('logged in: ',is_logged_in)
    print('\n')

    while True:
        account_info=mt.account_info()
        print(datetime.now(),
              '| Login:',account_info.login,
              '| Balance: ',account_info.balance,
              '| Equity: ', account_info.equity)
        
        num_positions=mt.positions_total()

        if not check_allowed_trading_hours():
            close_positions('all')
        
        fast_sma=get_sma(symbol,timeframe,10)
        slow_sma=get_sma(symbol,timeframe,100)

        if fast_sma>slow_sma:
            close_positions('sell')

            if num_positions==0 and check_allowed_trading_hours():
                order_result=market_order(symbol,volume,'buy')
                print(order_result)
        
        elif fast_sma<slow_sma:
            close_positions('buy')

            if num_positions==0 and check_allowed_trading_hours():
                order_result=market_order(symbol,volume,'sell')
                print(order_result)
        

        time.sleep(1)



