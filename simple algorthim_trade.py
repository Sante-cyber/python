import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
from datetime import datetime
from python.common import login,password,server


mt.login(login,password,server)

symbol='AUDUSD'
timeframe=mt.TIMEFRAME_M10
volume=0.1
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






def get_signal(x):
    if 9<=x['hour']<=18:
        if x['sma_10']>x['sma_100']:
            return 1
        elif x['sma_10']<x['sma_100']:
            return -1
    return 0

bars2['signal']=bars2.apply(get_signal,axis=1)
bars2['prev_price']=bars2['close'].shift(1)
bars2['price_change']=bars2['close']-bars2['prev_price']

bars2['signal_change']=(bars2['signal']-bars2['signal'].shift(1)).abs()
bars2['commission']=bars2.apply(lambda x:commission*x['signal_change']*x['trade_volume'],axis=1)*100000
bars2

bars3=bars2.dropna().copy()
bars3['profit']=bars3['signal']*bars3['price_change']*bars3['trade_volume']*100000
bars3['grossip_profit']=bars3['profit'].cumsum()
bars3['net_profit']=bars3['grossip_profit']-bars3['commission'].cumsum()
print(bars3)

fig=px.line(bars3,'time', ['grossip_profit','net_profit'],title='AUDUSD Backtest MA Trendfollowing')
fig.show()
