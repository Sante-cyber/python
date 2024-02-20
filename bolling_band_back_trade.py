import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
from common import login,password,server
import numpy as np
import time

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
        'sl':stoploss,
        'tp':takeprofit,
        "deviation":deviation,
        "comment":"python market order",
        "type_time":mt.ORDER_TIME_GTC,
        "type_filling":mt.ORDER_FILLING_IOC,
    }

    order_result=mt.order_send(request)
    return(order_result)

def get_signal(symbol):
    bars=mt.copy_rates_from_pos(symbol,TIMEFRAME,1,SMA_PERIOD)
    df=pd.DataFrame(bars)
    sma=df['close'].mean()
    sd=df['close'].std()
    lower_band=sma-STANDARD_DEVIATIONS*sd
    upper_band=sma-STANDARD_DEVIATIONS*sd
    last_close_price=df.iloc[-1]['close']
    if last_close_price<lower_band:
        return 'buy', sd
    elif last_close_price>upper_band:
        return 'sell',sd
    else:
        return [None,None]


if mt.initialize():
    print('connect to MetaTrader5')
    mt.login(login,password,server)

    TIMEFRAME=mt.TIMEFRAME_D1
    VOLUME=0.1
    DEVIATION=20
    MAGIC=10
    SMA_PERIOD=20
    STANDARD_DEVIATIONS=2
    TP_SD=2
    SL_SD=1

    symbols=mt.symbols_get()
    df=pd.DataFrame(symbols)
    a=df.iloc[:,[93,95]]
    a.reset_index(inplace=True)
    b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
    symbols=b[(~a.iloc[:,1].str.contains('.a'))]
    positions=mt.positions_get()
    positions_df=pd.DataFrame(positions,columns=positions[0]._asdict().keys())
    total_volume=positions_df['volume'].sum()
while total_volume<=3:

    for symbol in symbols.iloc[:,1]:
        signal=None
        print(f'Stragety symbol:{symbol}')
        if mt.positions_total()==0:
            signal,standard_deviation=get_signal(symbol)
            if signal is not None:
                print(f"It's good chance to {signal} to this symbol--{symbol}")
        else:
            positions=mt.positions_get()
            positions_df=pd.DataFrame(positions,columns=positions[0]._asdict().keys())
            if positions_df[positions_df['symbol']==symbol]['symbol'].count()==0:
                signal,standard_deviation=get_signal(symbol) 
                if signal is not None:
                    print(f"It's good chance to {signal} to this symbol--{symbol}")
        
        
        if signal=='buy':
            tick=mt.symbol_info_tick(symbol) 
            print(tick)
            result=market_order(symbol,VOLUME,signal,20,10,tick.bid-SL_SD*standard_deviation,tick.bid+TP_SD*standard_deviation)
            print(result)
        elif signal=='sell':
            tick=mt.symbol_info_tick(symbol) 
            print(tick)
            result=market_order(symbol,VOLUME,signal,20,10,tick.bid+SL_SD*standard_deviation,tick.bid-TP_SD*standard_deviation)
            print(result)
        else: print(f'there is no trade chance for this symbol--{symbol}')
        positions=mt.positions_get()
        positions_df=pd.DataFrame(positions,columns=positions[0]._asdict().keys())
        total_volume=positions_df['volume'].sum()

        time.sleep(1)



