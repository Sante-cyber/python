import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
from common import login_real,password_real,server_real
import numpy as np
import time
import schedule
import pandas_ta as ta
# import datetime
import pytz

# login=51658107
# password='VxBvOa*4'
# server='ICMarkets-Demo'



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
    df['rsi']=ta.rsi(df.close, length=14)
    df['overbought']=68
    df['oversold']=28
    df['time']=pd.to_datetime(df['time'],unit='s')
    df['hour']=df['time'].dt.hour
    sma=df['close'].mean()
    sd=df['close'].std()
    lower_band=sma-STANDARD_DEVIATIONS*sd
    upper_band=sma+STANDARD_DEVIATIONS*sd
    last_close_price=df.iloc[-1]['close']
    hour=df.iloc[-1]['hour']
    rsi=df.iloc[-1]['rsi']
    if last_close_price<lower_band:
        return 'buy', sd, last_close_price,upper_band,lower_band,hour
    elif last_close_price>upper_band:
        return 'sell',sd,last_close_price,upper_band,lower_band,hour
    else:
        return [None,sd,last_close_price,upper_band,lower_band,hour]





if mt.initialize():
    print('connect to MetaTrader5')
    # login=51658107
    # password='VxBvOa*4'
    # server='ICMarkets-Demo'
    mt.login(login_real,password_real,server_real)

    TIMEFRAME=mt.TIMEFRAME_H4
    VOLUME=0.02
    DEVIATION=5
    MAGIC=10
    SMA_PERIOD=20
    STANDARD_DEVIATIONS=2
    TP_SD=2
    SL_SD=1
    symbol='GBPAUD.a'

    # symbols=mt.symbols_get()
    # df=pd.DataFrame(symbols)
    # a=df.iloc[:,[93,95]]
    # a.reset_index(inplace=True)
    # b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
    # symbols=b[(~a.iloc[:,1].str.contains('.a'))]
    # positions=mt.positions_get()
    # if  len(positions) !=0:
    #    positions_df=pd.DataFrame(positions,columns=positions[0]._asdict().keys())
    #    total_volume=positions_df['volume'].sum()
    # else:
    #    total_volume=0

# Define Sydney time zone
sydney_tz = pytz.timezone('Australia/Sydney')

# Define GMT+3 time zone
gmt_tz = pytz.timezone('Etc/GMT-2')

# Get current time in Sydney
sydney_time = datetime.now(sydney_tz)

# Convert Sydney time to GMT+3
gmt_time = sydney_time.astimezone(gmt_tz)

print("Sydney Time:", sydney_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
print("GMT Time:", gmt_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'))

gmt_hour=gmt_time.hour


while True:
  
    signal=None
    print(f'Stragety symbol:{symbol}')
    
    if mt.positions_total()==0:
        signal,standard_deviation,last_close_price,upper_band,lower_band,hour=get_signal(symbol)
        if signal is not None:
            print(f"It's good chance to {signal} to this symbol--{symbol}")
    else:
       signal,standard_deviation,last_close_price,upper_band,lower_band,hour=get_signal(symbol)
       signal=None

    if signal=='buy':
        tick=mt.symbol_info_tick(symbol) 
        print(f'cuurently_bid_price_tick--{tick.ask}--less than {last_close_price} make order')
        if tick.ask<=last_close_price:
            result=market_order(symbol,VOLUME,signal,DEVIATION,10,tick.bid-SL_SD*standard_deviation,tick.ask+TP_SD*standard_deviation)
            print(signal,tick.bid,tick.ask,standard_deviation)
            print(result)
    elif signal=='sell':
        tick=mt.symbol_info_tick(symbol) 
        print(f'cuurently_bid_price_tick--{tick.bid}--bigger than {last_close_price} can make order')
        if tick.bid>=last_close_price:
            result=market_order(symbol,VOLUME,signal,DEVIATION,10,tick.ask+SL_SD*standard_deviation,tick.bid-TP_SD*standard_deviation)
            print(signal,tick.bid,tick.ask,standard_deviation)
            print(result)
    else: print(f'there is no trade chance for this symbol--{symbol}--last_close_price--{last_close_price}--upper_band--{upper_band}--lower_band--{lower_band}--hour--{hour}')

    time.sleep(60)



