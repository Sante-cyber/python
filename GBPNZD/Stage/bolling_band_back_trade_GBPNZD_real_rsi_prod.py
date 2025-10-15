import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
from common import login_real,password_real,server_real
# from common import login,password,server
import numpy as np
import time
import schedule
import pandas_ta as ta
import talib as ta1
# import datetime
import pytz
import os
import traceback


def set_profit_loss(data,order_price,trade_signal):
    if trade_signal=='sell':
        if data.sd>0.01:
            tp=order_price-0.01*order_price  
            sl=order_price+0.01*order_price
        elif data.sd>0.009:
            tp=order_price-0.007*order_price  
            sl=order_price+0.008*order_price
        else:
            tp=order_price-0.005*order_price  
            sl=order_price+0.007*order_price
    elif trade_signal=='buy':
        if data.sd>0.01:
            tp=order_price+0.01*order_price  
            sl=order_price-0.01*order_price
        elif data.sd>0.009:
            tp=order_price+0.007*order_price  
            sl=order_price-0.008*order_price
        else:
            tp=order_price+0.005*order_price  
            sl=order_price-0.007*order_price
    return tp,sl

def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=30
    return data



def find_lower_high_point(df,type):
    for i in range(1, len(df) - 1):
        if df[type][i] > df[type][i - 1] and df[type][i] > df[type][i + 1]:
            df.at[i, 'high_point'] = 1
        elif df[type][i] < df[type][i - 1] and df[type][i] < df[type][i + 1]:
            df.at[i, 'low_point'] = 1
    
    return(df)

def count_consecutive_above(df, column_name,number):
    consecutive_counts = []  # List to store counts for each row
    count = 0  # Initialize count of consecutive rows
    for value in df[column_name]:  # Iterate over values in the specific column
        if value >= number:  # If the value is greater than 70
            count += 1  # Increment the count of consecutive rows
        else:
            count = 0  # Reset the count if the value is not greater than 70
        consecutive_counts.append(count)  # Append the count for the current row
    return consecutive_counts

def count_consecutive_lower(df, column_name,number):
    consecutive_counts = []  # List to store counts for each row
    count = 0  # Initialize count of consecutive rows
    for value in df[column_name]:  # Iterate over values in the specific column
        if value <= number:  # If the value is lower than 30
            count += 1  # Increment the count of consecutive rows
        else:
            count = 0  # Reset the count if the value is not greater than 30
        consecutive_counts.append(count)  # Append the count for the current row
    return consecutive_counts


def find_signal(close,lower_band,upper_band,rsi,overbought,oversold):
        if close<lower_band and rsi<oversold:
            return 'buy'
        elif close>upper_band and rsi>overbought:
            return 'sell'

def count_signal_buy(df, column_name):
    buy_counts = []  # List to store counts for each row
    count = 0  # Initialize count of consecutive rows
    for value in df[column_name]:  # Iterate over values in the specific column
        if value =='buy':  # If the value is lower than 30
            count += 1  # Increment the count of consecutive rows
        else:
            count = 0  # Reset the count if the value is not greater than 30
        buy_counts.append(count)  # Append the count for the current row
    return buy_counts


def count_signal_sell(df, column_name):
    buy_counts = []  # List to store counts for each row
    count = 0  # Initialize count of consecutive rows
    for value in df[column_name]:  # Iterate over values in the specific column
        if value =='sell':  # If the value is lower than 30
            count += 1  # Increment the count of consecutive rows
        else:
            count = 0  # Reset the count if the value is not greater than 30
        buy_counts.append(count)  # Append the count for the current row
    return buy_counts


def market_order(symbol,volume,order_type,deviation,magic,stoploss,takeprofit):
    magic=int(magic*10000)
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
        'tp':takeprofit,
        "deviation":deviation,
        "comment":"python market order",
        "type_time":mt.ORDER_TIME_GTC,
        "type_filling":mt.ORDER_FILLING_IOC,
    }
    print(request)
    
    if stoploss is not None:
       request['sl'] = stoploss

    order_result=mt.order_send(request)
    return(order_result)


def get_realtime_data(symbol,TIMEFRAME,SMA_PERIOD):
    
    bars=mt.copy_rates_from_pos(symbol,TIMEFRAME,1,SMA_PERIOD)
    df=pd.DataFrame(bars)
    df['time']=pd.to_datetime(df['time'],unit='s')
    df['hour']=df['time'].dt.hour
    
    df['sma']=df['close'].rolling(20).mean()
    df['sd']=df['close'].rolling(20).std()
    df['lb']=df['sma']-STANDARD_DEVIATIONS*df['sd']
    df['ub']=df['sma']+STANDARD_DEVIATIONS*df['sd']
    # doji
    df['doji'] = ta1.CDLDOJI(df['open'], df['high'], df['low'], df['close'])

    # hammer
    df['hammer'] = ta1.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])

    # hanging man
    df['hanging man'] = ta1.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])

    # shooting star
    df['shooting star'] = ta1.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])

    # inverted hammer
    df['inverted hammer'] = ta1.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])

    # spinning top
    df['spinning top'] = ta1.CDLSPINNINGTOP(df['open'], df['high'], df['low'], df['close'])

    # marubozu
    df['marubozu'] = ta1.CDLMARUBOZU(df['open'], df['high'], df['low'], df['close'])

    # long-legged doji
    df['long-legged doji'] = ta1.CDLLONGLEGGEDDOJI(df['open'], df['high'], df['low'], df['close'])

    # dragonfly doji
    df['dragonfly doji'] = ta1.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])

    # gravestone doji
    df['gravestone doji'] = ta1.CDLGRAVESTONEDOJI(df['open'], df['high'], df['low'], df['close'])
    
    
    # bearish engulfing pattern
    df['bearish_engulfing'] = ta1.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])

    # piercing pattern
    df['piercing_pattern'] = ta1.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])

    # dark cloud cover
    df['dark_cloud_cover'] = ta1.CDLDARKCLOUDCOVER(df['open'], df['high'], df['low'], df['close'])

    # harami pattern
    df['harami_pattern'] = ta1.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
    
    df['inside_bar'] = ((df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))).astype(int)
    
    
    df=find_lower_high_point(df,'tick_volume')
    
    df=rsi(df,14)
    df['low_rsi']=ta.rsi(df.low, length=14)
    df['high_rsi']=ta.rsi(df.high, length=14)
    df['over_70_high'] = count_consecutive_above(df, 'high_rsi',70)
    df['lower_30_high'] = count_consecutive_lower(df, 'high_rsi',30)
    df['over_70_low'] = count_consecutive_above(df, 'low_rsi',70)
    df['lower_30_low'] = count_consecutive_lower(df, 'low_rsi',30)
    df['over_70'] = count_consecutive_above(df, 'rsi',70)
    df['lower_30'] = count_consecutive_lower(df, 'rsi',30)
    
    
    df.dropna(subset=['sd'], inplace=True)
 
    
    df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'],df['rsi'],df['overbought'],df['oversold'])
    df['buy_cnt']=count_signal_buy(df,'signal')
    df['sell_cnt']=count_signal_sell(df, 'signal')
    df.reset_index(inplace=True)
    # df.to_csv(f'E:/EA/bollinger-bands/H4_year/b_{year}_opi_5.0.csv')
    return df
    
    
def get_strategy(df):    
    is_trade=0
    trade_signal=None
    data=df.iloc[-1]
    pre_row=df.iloc[-2]
    pre_2_row=df.iloc[-3]

    if is_trade==0  \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and data.buy_cnt==0 and data.lower_30==0:
        is_trade=1.1
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1\
        and data.buy_cnt==0 and data.lower_30==2:
        is_trade=1.2
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1  \
        and data.buy_cnt==2:
        is_trade=1.3
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2  \
        and data.buy_cnt==0 and data.lower_30==0:
        is_trade=1.4
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2  \
        and data.buy_cnt==0 and  data.lower_30>0:
        is_trade=1.5
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>1  \
        and data.buy_cnt==2:
        is_trade=1.6
        trade_signal='buy'
    elif is_trade==0 \
        and pre_row.rsi>30 and pre_row.rsi<32 and data.rsi>32 and pre_row.close<pre_row.lb:
        is_trade=1.7
        trade_signal='buy'
    elif is_trade==0   \
        and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 and data.sell_cnt==0  and data.over_70==0:
        is_trade=2.1
        trade_signal='sell'
    elif is_trade==0 \
        and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 \
        and data.sell_cnt==0 and data.over_70==2:
        is_trade=2.2
        trade_signal='sell'
    elif is_trade==0 \
        and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1  \
        and data.sell_cnt==2:
        # print(data.time)
        is_trade=2.3
        trade_signal='sell'
    elif is_trade==0 \
        and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70>1  \
        and data.sell_cnt==2:
        is_trade=2.4
        trade_signal='sell'
    elif is_trade==0 \
        and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70>1 \
        and data.sell_cnt==0:
        is_trade=2.5
        trade_signal='sell'
    elif is_trade==0 \
        and pre_row.rsi>68 and pre_row.rsi<70 and data.rsi<68 and pre_row.close>pre_row.ub:
        is_trade=2.6
        trade_signal='sell'
    return trade_signal,is_trade,data,pre_row,pre_2_row

def run_strategy(is_trade,signal,data,pre_row,pre_2_row,VOLUME,tick,take_action):
    
    # tick=mt.symbol_info_tick(symbol) 
    
    result=None
    
    action=take_action
    
    print(f'cuurently_time--{tick.time}--cuurently_buy_price_tick--{tick.ask}--cuurently_sell_price_tick--{tick.bid}--last_close--{data.close}--signal--{signal}--strategy--{is_trade}')
    
    if is_trade==1.1:
        if pre_row.high_rsi>30 and pre_row.high_rsi>pre_row.low_rsi and pre_row.low_rsi>pre_row.rsi and data.lower_30_low!=1:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price
                is_trade=1.11  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi>30 and pre_row.high_rsi>pre_row.low_rsi and pre_row.low_rsi>pre_row.rsi and data.lower_30_low==1\
            and data.low_rsi>data.high_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price  
                is_trade=1.12   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi>30 and pre_row.high_rsi>pre_row.low_rsi and pre_row.low_rsi<pre_row.low_rsi: 
            is_trade=3.11 
            action=None
            signal='sell'
        elif pre_row.high_rsi>30 and pre_row.high_rsi<pre_row.low_rsi and data.low_rsi> pre_row.low_rsi and data.high_rsi>pre_row.high_rsi:
            order_price=data.close                          
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price  
                is_trade=1.13   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi>30 and pre_row.high_rsi<pre_row.low_rsi: 
            is_trade=3.12 
            action=None
            signal='sell'
        elif pre_row.high_rsi<30 and  pre_row.high_rsi>pre_row.low_rsi and data.low_rsi>30:
            order_price=data.close 
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price  
                is_trade=1.14   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi<30 and  pre_row.high_rsi>pre_row.low_rsi: 
            is_trade=3.13 
            action=None
            signal='sell'
        elif pre_row.high_rsi<30 and pre_row.high_rsi<pre_row.low_rsi and pre_row.low_rsi>30 and (pre_row.high_point>0 or pre_row.low_point>0): 
            order_price=data.close 
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price  
                is_trade=1.15   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1         
        elif pre_row.high_rsi<30 and  pre_row.high_rsi<pre_row.low_rsi and pre_row.low_rsi>30: 
            is_trade=3.141 
            action=None
            signal='sell'
        elif pre_row.high_rsi<30 and pre_row.high_rsi<pre_row.low_rsi and pre_row.low_rsi<30 \
            and data.lower_30_low>=data.lower_30_high and data.low_rsi>pre_row.low_rsi:
            order_price=data.close 
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.008*order_price
                tp=order_price+0.007*order_price  
                is_trade=1.16   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi<30 and pre_row.high_rsi<pre_row.low_rsi and pre_row.low_rsi<30 \
            and data.lower_30_low>=data.lower_30_high and data.low_rsi<pre_row.low_rsi and pre_row.low_rsi<pre_2_row.low_rsi\
            and data.high_rsi<pre_row.high_rsi:
            order_price=data.close 
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.008*order_price
                tp=order_price+0.007*order_price  
                is_trade=1.17   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.1
        elif pre_row.high_rsi<30 and pre_row.high_rsi<pre_row.low_rsi and pre_row.low_rsi<30: 
            is_trade=3.142 
            action=None
            signal='sell'   
    elif is_trade==1.2:
        if data.lower_30==0 and pre_row.low_rsi<30:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.2
        elif data.lower_30==0:
            is_trade=3.2 
            action=None
            signal='sell' 
    elif is_trade==1.3:
        if data.buy_cnt==0 and pre_row.buy_cnt==2 and data.low_rsi>max(data.high_rsi,data.rsi) and data.low_rsi<30:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.007*order_price
                tp=order_price+0.006*order_price
                is_trade=1.31
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
        elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.low_rsi>max(data.high_rsi,data.rsi):
            is_trade=3.31
            action=None
            signal='sell'  
        elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.low_rsi<max(data.high_rsi,data.rsi) and (data.low_rsi<30 or data.high_rsi<30):
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.007*order_price
                tp=order_price+0.0055*order_price
                is_trade=1.32
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
        elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.low_rsi<max(data.high_rsi,data.rsi):
            is_trade=3.32
            action=None
            signal='sell'  
        elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.low_rsi>pre_row.low_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                if data.sd>0.0097:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:     
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price
                is_trade=1.331
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
        elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.low_rsi<pre_row.low_rsi and data.low_rsi>max(data.rsi,data.high_rsi):
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price
                is_trade=1.332 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
        elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.low_rsi<pre_row.low_rsi and data.low_rsi<max(data.rsi,data.high_rsi)\
            and data.low_rsi<min(data.high_rsi,data.rsi) and pre_row.low_rsi>pre_row.high_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price
                is_trade=1.333 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
        elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.low_rsi<pre_row.low_rsi:
            is_trade=3.33
            action=None
            signal='sell'  
        elif data.buy_cnt==0 and pre_row.buy_cnt>3:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:     
                    sl=order_price-0.007*order_price
                    tp=order_price+0.006*order_price
                is_trade=1.34
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.3
    elif is_trade==1.4:
        if data.low_rsi>pre_row.low_rsi :
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price      
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=1.4 
        else:
            is_trade=3.4
            action=None
            signal='sell'  
    elif  is_trade==1.5:
        if pre_row.lower_30>0 and data.lower_30==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else: 
                    tp=order_price+0.005*order_price
                    sl=order_price-0.006*order_price     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.5   
    elif  is_trade==1.6:
        if pre_row.buy_cnt>0 and data.buy_cnt==0 and data.lower_30==0:
                is_trade=3.61
                action=None
                signal='sell'             
        elif pre_row.buy_cnt>0 and data.buy_cnt==0 and data.lower_30>0:
            is_trade=1.62
            action=None
    elif is_trade==1.62:
        if  pre_row.lower_30>0 and data.lower_30==0 and pre_row.low_rsi>max(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.005*order_price
                sl=order_price-0.006*order_price
                is_trade=1.62
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.62
        elif pre_row.lower_30>0 and data.lower_30==0:
                is_trade=3.62
                action=None
                signal='sell'   
    elif is_trade==1.7:
        if data.high_rsi>pre_row.high_rsi and data.low_rsi>pre_row.low_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.005*order_price
                sl=order_price-0.006*order_price  
                is_trade=1.71   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=1.7
        elif data.high_rsi>pre_row.high_rsi and data.low_rsi<pre_row.low_rsi \
            and pre_row.low_rsi>pre_row.high_rsi and pre_row.low_rsi<max(pre_row.rsi,pre_row.high_rsi) \
            and pre_row.lower_30_high<=pre_row.lower_30_low:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.005*order_price
                sl=order_price-0.006*order_price  
                is_trade=1.72   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=1.7
        elif data.high_rsi>pre_row.high_rsi:
                is_trade=3.71
                action=None
                signal='sell'
        elif data.high_rsi<pre_row.high_rsi and pre_row.rsi<min(pre_row.low_rsi,pre_row.high_rsi) and pre_row.low_rsi<pre_row.high_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.006*order_price
                sl=order_price-0.007*order_price
                is_trade=1.73    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.7
        elif data.high_rsi<pre_row.high_rsi and pre_row.rsi>max(pre_row.low_rsi,pre_row.high_rsi) and pre_row.low_rsi>pre_row.high_rsi:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.006*order_price
                sl=order_price-0.007*order_price
                is_trade=1.74    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.7
        elif data.high_rsi<pre_row.high_rsi and data.rsi>max(data.low_rsi,data.high_rsi) and data.low_rsi>data.high_rsi \
            and pre_2_row.rsi>pre_2_row.low_rsi and data.lower_30_high>=data.lower_30_low:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.006*order_price
                sl=order_price-0.007*order_price
                is_trade=1.75    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=1.7
        elif data.high_rsi<pre_row.high_rsi:
            is_trade=3.72
            action=None
            signal='sell'     
    elif is_trade==2.1:
        if data.high_rsi<pre_row.high_rsi and data.low_rsi>70:
            order_price=data.close   
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    sl=order_price+0.01*order_price
                    tp=order_price-0.01*order_price
                else:
                    sl=order_price+0.007*order_price
                    tp=order_price-0.006*order_price
                is_trade=2.11  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi<pre_row.high_rsi and data.low_rsi<70 and data.low_rsi>pre_row.low_rsi:
            order_price=data.close   
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    sl=order_price+0.018*order_price
                    tp=order_price-0.01*order_price
                else:
                    sl=order_price+0.007*order_price
                    tp=order_price-0.005*order_price
                is_trade=2.12  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi<pre_row.high_rsi and data.low_rsi<70 and data.low_rsi<pre_row.low_rsi and data.low_rsi>max(data.rsi,data.high_rsi):
            order_price=data.close   
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.13  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi<pre_row.high_rsi and data.low_rsi<70 and data.low_rsi<pre_row.low_rsi and data.low_rsi<min(data.rsi,data.high_rsi):
            order_price=data.close   
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.14  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi<pre_row.high_rsi:
                is_trade=4.11
                action=None
                signal='buy'
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi<72  and pre_row.rsi>max(pre_row.low_rsi,pre_row.high_rsi) and pre_row.low_rsi<70:
            order_price=data.close   
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.008*order_price
                tp=order_price-0.007*order_price  
                is_trade=2.15  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi<72 and pre_row.rsi>max(pre_row.low_rsi,pre_row.high_rsi):
                is_trade=4.12
                action=None
                signal='buy'
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi<72 and pre_row.rsi<max(pre_row.low_rsi,pre_row.high_rsi) \
            and data.low_rsi<pre_row.rsi and data.sd>=0.008:
            if tick.bid>=order_price:
                sl=order_price+0.009*order_price
                tp=order_price-0.008*order_price
                is_trade=2.16  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi<72 and pre_row.rsi<max(pre_row.low_rsi,pre_row.high_rsi) \
            and data.low_rsi<pre_row.rsi and  data.sd<0.008 and pre_row.low_rsi<60:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp=order_price-0.005*order_price 
                sl=order_price+0.006*order_price
                is_trade=2.17  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi<72 and pre_row.rsi<max(pre_row.low_rsi,pre_row.high_rsi):  
            is_trade=4.13
            action=None
            signal='buy'
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi>72 and pre_row.sd>0.01:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.01*order_price
                tp=order_price-0.01*order_price
                is_trade=2.18 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi>pre_row.high_rsi and pre_row.rsi>72 and pre_row.sd<0.01 \
            and pre_row.low_rsi>70 and data.low_rsi<pre_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.191
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif data.high_rsi==pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.192
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.1
        elif pre_row.high_rsi>70 and pre_row.low_rsi>min(pre_row.high_rsi,pre_row.rsi):  
            is_trade=4.14
            action=None
            signal='buy'                                               
    elif is_trade==2.2:
        if pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi>max(pre_row.low_rsi,pre_row.rsi) \
            and data.low_rsi>min(data.rsi,data.high_rsi) and data.rsi<66:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    sl=order_price+0.01*order_price
                    tp=order_price-0.01*order_price
                else:
                    sl=order_price+0.006*order_price
                    tp=order_price-0.005*order_price
                is_trade=2.21    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.2
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi>max(pre_row.low_rsi,pre_row.rsi) \
            and data.low_rsi>min(data.rsi,data.high_rsi) and data.rsi>=66:  
            is_trade=4.21
            action=None
            signal='buy'    
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi>max(pre_row.low_rsi,pre_row.rsi) \
            and data.low_rsi<min(data.rsi,data.high_rsi) and data.rsi>max(data.low_rsi,data.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price 
                is_trade=2.22     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.2
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi>max(pre_row.low_rsi,pre_row.rsi)\
            and data.low_rsi<min(data.rsi,data.high_rsi):
                is_trade=4.22
                action=None
                signal='buy'
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi<max(pre_row.low_rsi,pre_row.rsi) \
            and pre_row.rsi>max(pre_row.low_rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price 
                is_trade=2.23     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.2
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi<max(pre_row.low_rsi,pre_row.rsi) \
            and pre_row.rsi<max(pre_row.low_rsi,pre_row.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price 
                is_trade=2.24     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.2
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.high_rsi<max(pre_row.low_rsi,pre_row.rsi):
                is_trade=4.23
                action=None
                signal='buy'
    elif is_trade==2.3:
        if  pre_row.sell_cnt==2 and data.sell_cnt==0 and data.over_70==0 and data.low_rsi>pre_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.03:
                    sl=order_price+0.03*order_price
                    tp=order_price-0.01*order_price
                elif data.sd>0.02:
                    sl=order_price+0.02*order_price
                    tp=order_price-0.01*order_price
                elif data.sd>0.01:
                    sl=order_price+0.01*order_price
                    tp=order_price-0.01*order_price
                else:
                    sl=order_price+0.007*order_price
                    tp=order_price-0.006*order_price
                is_trade=2.311
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.3
        elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.over_70==0 and data.low_rsi<pre_row.low_rsi \
            and data.high_rsi>data.low_rsi and data.low_rsi>data.rsi and data.high_rsi<pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.009*order_price
                tp=order_price-0.008*order_price
                is_trade=2.312
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.3
        elif pre_row.sell_cnt==3 and data.sell_cnt==0 and data.over_70==0 and data.low_rsi>max(data.rsi,data.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.009*order_price
                tp=order_price-0.008*order_price
                is_trade=2.32
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.3
        elif pre_row.sell_cnt>=2 and data.sell_cnt==0 and data.over_70==0:
                is_trade=4.31
                action=None
                signal='buy'
        elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.over_70>0:
            is_trade=2.33
            action=None
        elif pre_row.sell_cnt>2 and data.sell_cnt==0 and data.over_70>0:
            is_trade=2.34
            action=None
    elif is_trade==2.33:
        if pre_row.over_70==3 and data.over_70==0 and data.high_rsi>pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.331
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.33
        elif pre_row.over_70==3 and data.over_70==0:
                is_trade=4.321
                action=None
                signal='buy'
        elif pre_row.over_70>3 and data.over_70==0 and pre_2_row.high_rsi<pre_row.high_rsi and pre_row.high_rsi<data.high_rsi\
            and pre_row.low_rsi>pre_2_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                is_trade=2.332
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.33
        elif pre_row.over_70>3 and data.over_70==0 and pre_2_row.high_rsi<pre_row.high_rsi:
                is_trade=4.322
                action=None
                signal='buy'
        elif pre_row.over_70>3 and data.over_70==0 and pre_2_row.high_rsi>pre_row.high_rsi and pre_row.high_rsi>data.high_rsi\
            and data.low_rsi>max(data.rsi,data.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.01*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.333
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.33
        elif pre_row.over_70>3 and data.over_70==0 and pre_2_row.high_rsi>pre_row.high_rsi and pre_row.high_rsi>data.high_rsi\
            and data.low_rsi<min(data.rsi,data.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.334
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.33
        elif pre_row.over_70>3 and data.over_70==0 and pre_2_row.high_rsi>pre_row.high_rsi and pre_row.high_rsi>data.high_rsi\
            and pre_row.low_rsi>pre_2_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.335
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.33
        elif pre_row.over_70>3 and data.over_70==0:
                is_trade=4.323
                action=None
                signal='buy'
    elif is_trade==2.34:
        if pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi<80\
            and data.low_rsi<pre_row.low_rsi and data.low_rsi<70 and pre_row.low_rsi<max(pre_row.rsi,pre_row.high_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.341
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.34
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi<80\
            and data.low_rsi<pre_row.low_rsi and data.low_rsi>70 and data.high_rsi>pre_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.342
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.34
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi<80\
            and data.low_rsi>pre_row.low_rsi and data.high_rsi>pre_row.high_rsi and pre_2_row.high_rsi>pre_2_row.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.343
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.34
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi<80\
            and data.low_rsi>pre_row.low_rsi and data.high_rsi<pre_row.high_rsi and data.low_rsi>data.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.344
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.34
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi<80:
                is_trade=4.331
                action=None
                signal='buy'
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi>80:
                is_trade=4.332
                action=None
                signal='buy'                              
    elif is_trade==2.4:
        if pre_row.sell_cnt>0 and data.sell_cnt==0 and data.over_70==0:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.41   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.4
        elif pre_row.sell_cnt>0 and data.sell_cnt==0 and data.over_70>0:
                is_trade=2.42 
                action=None
    elif is_trade==2.42 :
        if pre_row.over_70>0 and data.over_70==0:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    tp=order_price-0.01*order_price  
                    sl=order_price+0.015*order_price
                elif data.sd>0.009:
                    tp=order_price-0.007*order_price  
                    sl=order_price+0.008*order_price
                else:
                    tp=order_price-0.005*order_price  
                    sl=order_price+0.006*order_price
                is_trade=2.42 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.42    
    elif is_trade==2.5 :
        if pre_row.over_70>0 and data.over_70==0 and data.low_rsi>max(pre_row.rsi,pre_row.high_rsi) :
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                is_trade=2.51
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.5
        elif pre_row.over_70>0 and data.over_70==0 and data.low_rsi<max(pre_row.rsi,pre_row.high_rsi)\
            and pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and data.high_rsi<pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal)   
                is_trade=2.52
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.5
        elif pre_row.over_70>0 and data.over_70==0:
            is_trade=4.5
            action=None
            signal='buy'
    elif is_trade==2.6:  
        if pre_row.low_rsi>max(pre_row.rsi,pre_row.high_rsi) and data.low_rsi<pre_row.low_rsi :                           
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal)  
                is_trade=2.61  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6       
        elif pre_row.low_rsi>max(pre_row.rsi,pre_row.high_rsi) and data.low_rsi>pre_row.low_rsi and data.high_rsi>pre_row.high_rsi:                                
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                is_trade=2.62 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:
                action=2.6
        elif pre_row.low_rsi>max(pre_row.rsi,pre_row.high_rsi):
            is_trade=4.61
            action=None
            signal='buy' 
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) \
            and data.high_rsi>70 and pre_row.high_rsi>70 \
            and data.close<data.ub and data.low_rsi<70\
            and data.sd>0.006: 
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                is_trade=2.63  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) \
            and data.high_rsi>70 and pre_row.high_rsi>70:                     
                is_trade=4.62
                action=None
                signal='buy'
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) \
            and data.high_rsi<70 and pre_row.high_rsi<70 \
            and pre_2_row.high_rsi<60 and pre_row.low_rsi<60:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                is_trade=2.64
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6 
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi)\
            and data.high_rsi<70 and pre_row.high_rsi<70 and pre_2_row.low_point!=1 and pre_2_row.high_point!=1:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                is_trade=2.65
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6 
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi)\
            and data.high_rsi<70 and pre_row.high_rsi<70:
            is_trade=4.63
            action=None
            signal='buy'
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi)\
            and data.low_rsi>70:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                is_trade=2.66 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6
        elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi):
            is_trade=4.64
            action=None
            signal='buy'
        elif pre_row.high_rsi>70 and data.high_rsi>data.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                is_trade=2.67 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6
        elif pre_row.high_rsi>70 and data.high_rsi<data.low_rsi and pre_row.low_point==1:
            order_price=data.close
            if tick.bid>=order_price:
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                is_trade=2.68
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6
        elif  pre_row.high_rsi>70:
            is_trade=4.65
            action=None
            signal='buy'
        elif data.low_rsi>data.high_rsi and data.sd>0.005:
            order_price=data.close
            if tick.bid>=order_price:
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                is_trade=2.69
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=2.6
        else:
            is_trade=4.66
            action=None
            signal='buy'
    elif is_trade==3.11:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.11
    elif is_trade==3.12:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.12
    elif is_trade==3.13:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.008:
                    sl=order_price+0.008*order_price
                    tp=order_price-0.007*order_price
                else:
                    sl=order_price+0.006*order_price
                    tp=order_price-0.005*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.13
    elif is_trade==3.141:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.009:
                    sl=order_price+0.008*order_price
                    tp=order_price-0.007*order_price
                else:
                    sl=order_price+0.006*order_price
                    tp=order_price-0.005*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.141
    elif is_trade==3.142:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.142              
    elif is_trade==3.2 :                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.2
    elif is_trade==3.31:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.31
    elif is_trade==3.32:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.32
    elif is_trade==3.33:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.33
    elif is_trade==3.4:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=3.4        
    elif is_trade==3.61:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: action=3.61 
    elif is_trade==3.62:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                if data.sd>0.01:
                    sl=order_price+0.01*order_price
                    tp=order_price-0.01*order_price
                else:
                    sl=order_price+0.006*order_price
                    tp=order_price-0.005*order_price   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: action=3.62  
    elif is_trade==3.71:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price
                tp=order_price-0.005*order_price   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: action=3.71 
    elif is_trade==3.72:                            
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.007*order_price
                tp=order_price-0.006*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: action=3.72           
    elif is_trade==4.11:                            
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.11
    elif is_trade==4.12:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd<0.004:
                    sl=order_price-0.009*order_price
                    tp=order_price+0.008*order_price 
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.12
    elif is_trade==4.13:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.13
    elif is_trade==4.14:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price   
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.14
    elif is_trade==4.21:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                sl=order_price-0.006*order_price
                tp=order_price+0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.21 
    elif is_trade==4.22:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price   
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price   
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.22 
    elif is_trade==4.23:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price   
                else:
                    sl=order_price-0.007*order_price
                    tp=order_price+0.006*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.23
    elif is_trade==4.31:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price   
                else:
                    sl=order_price-0.007*order_price
                    tp=order_price+0.006*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.31
    elif is_trade==4.321:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.321 
    elif is_trade==4.321:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.321 
    elif is_trade==4.322:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.322
    elif is_trade==4.323:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price    
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.323  
    elif is_trade==4.331:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.331 
    elif is_trade==4.332:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                if data.sd>0.01:
                    sl=order_price-0.01*order_price
                    tp=order_price+0.01*order_price
                else:
                    sl=order_price-0.006*order_price
                    tp=order_price+0.005*order_price     
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.332
    elif is_trade==4.5:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp,sl=set_profit_loss(data,order_price,trade_signal)
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.5
    elif is_trade==4.61:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.61
    elif is_trade==4.62:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp=order_price+0.007*order_price  
                sl=order_price-0.009*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.62   
    elif is_trade==4.63:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp=order_price+0.007*order_price  
                sl=order_price-0.009*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.63   
    elif is_trade==4.64:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp=order_price+0.007*order_price  
                sl=order_price-0.009*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.64  
    elif is_trade==4.65:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.65     
    elif is_trade==4.66:                            
            order_price=data.close
            if tick.ask<=order_price :
                order_price=tick.ask
                tp,sl=set_profit_loss(data,order_price,trade_signal) 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: 
                action=4.66 
    return result,signal,is_trade,data.time,action




if mt.initialize():
    print('connect to MetaTrader5')
    mt.login(login_real,password_real,server_real)
    # mt.login(login,password,server)
    
    TIMEFRAME=mt.TIMEFRAME_H4
    VOLUME=0.1
    DEVIATION=5
    MAGIC=10
    SMA_PERIOD=365
    STANDARD_DEVIATIONS=2
    TP_SD=2
    SL_SD=1
    symbol='GBPNZD.a'
    trade_signal=None
    trade_strategy=0


base_symbol = symbol.split('.')[0]  # -> EURAUD

log_path = os.getcwd()  # current working directory

log_folder_path= os.path.join(log_path, "python", base_symbol,"Data")

file_path = os.path.join(log_folder_path,"make_order.csv")


# Define Sydney time zone
sydney_tz = pytz.timezone('Australia/Sydney')


# Define GMT+3 time zone
gmt_tz = pytz.timezone('Etc/GMT-2')

# Get current time in Sydney
sydney_time = datetime.now(sydney_tz)
sydney_date=sydney_time.date()

# Convert Sydney time to GMT+3
gmt_time = sydney_time.astimezone(gmt_tz)

print("Sydney Time:", sydney_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
print("GMT Time:", gmt_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'))

gmt_hour=gmt_time.hour

last_order_date=None

action=None
action_time=None

log_file_path=f'{log_folder_path}/trade_log_{sydney_date}.txt'

while True:
    sydney_time = datetime.now(sydney_tz)
    sydney_date=sydney_time.date()
    try:
        print(f'Strategy symbol: {symbol}')
        
        positions = len(mt.positions_get(symbol=symbol))

        print(f'now the {symbol} order number is {positions}')
        
        make_order = pd.read_csv(file_path)
        
        if positions <= 3 and trade_strategy == 0:
            symbol_df = get_realtime_data(symbol, TIMEFRAME, SMA_PERIOD)
            
            trade_signal, trade_strategy, record, pre_record, pre_2_record = get_strategy(symbol_df)
            
            if trade_strategy > 0:
                make_order['strategy_time'] = record.time.strftime('%Y-%m-%d %H')
                make_order['strategy'] = trade_strategy
                make_order['trade_signal'] = trade_signal
                make_order.to_csv(file_path, index=False)
                print(f"It's a good chance to {trade_signal} this symbol -- {symbol}, the strategy is {trade_strategy}")
                with open(log_file_path, "a") as f:
                    f.write(f"Order time: {record.time.strftime('%Y-%m-%d %H')}, It's a good chance to {trade_signal} "
                            f"this symbol -- {symbol}, the strategy is {trade_strategy}\n")
            else:
                pre_trade_strategy = make_order['strategy'].iloc[-1]
                strategy_time = make_order['strategy_time'].iloc[-1]
                if pre_trade_strategy > 0:
                    trade_strategy = pre_trade_strategy
                    trade_signal = make_order['trade_signal'].iloc[-1]
                    print(f'The program terminated unnaturally, now continuing... '
                      f'Trade strategy time: {strategy_time}, trade strategy: {trade_strategy}, '
                      f'trade signal: {trade_signal}')
                    with open(log_file_path, "a") as f:
                        f.write(f"The program terminated unnaturally, now continuing... "
                                f"Trade strategy time: {strategy_time}, trade strategy: {trade_strategy}, " 
                                f"trade signal: {trade_signal}\n")
        else:
            symbol_df = get_realtime_data(symbol, TIMEFRAME, SMA_PERIOD)
            record, pre_record, pre_2_record = get_strategy(symbol_df)[2:]

        tick = mt.symbol_info_tick(symbol)
        tick_date = record.time.strftime('%Y-%m-%d %H')
        
        if trade_strategy > 0 and last_order_date != tick_date:
            print(f'Starting run -- {trade_strategy}')

            pre_trade_strategy = make_order['strategy'].iloc[-1]

            
            result, trade_signal, trade_strategy, order_time, action = run_strategy(
                trade_strategy, trade_signal, record, pre_record, pre_2_record, 
                VOLUME, tick, action)
            
            if trade_strategy != pre_trade_strategy and trade_strategy > 0:
                make_order['strategy_time'] = record.time.strftime('%Y-%m-%d %H')
                make_order['strategy'] = trade_strategy
                make_order['trade_signal'] = trade_signal
                
                
            if action is not None:
                
                if action_time is None:
                    action_time = order_time
                    
                if action == trade_strategy and trade_strategy > 0 and action_time == order_time:
                    action = 0
                else:
                    trade_strategy = 0
                    make_order['strategy'] = trade_strategy
                    action = None
                    action_time = None
                    make_order['trade_signal'] = None
            
            if result is not None:
                action = None
                action_time = None
                make_order['strategy'] = 0
                make_order['trade_signal'] = None
                print(result)
                with open(log_file_path, "a") as f:
                    f.write(f"result: {result}\n")
                last_order_date = order_time.strftime('%Y-%m-%d %H')
                print(f'Order time: {last_order_date}, signal: {trade_signal}, '
                      f'after trade strategy: {trade_strategy}')
                with open(log_file_path, "a") as f:
                    f.write(f"Order time: {last_order_date}, signal: {trade_signal}, "
                            f"after trade strategy: {trade_strategy}\n")
                    
            elif action is None and trade_strategy==0:
                make_order['strategy'] = 0
                make_order['trade_signal'] = None
                print(f'This situation have not never happened in history,please notice this new situation,the trade strategy is {pre_trade_strategy}')
                with open(log_file_path, "a") as f:
                    f.write(f"This situation have not never happened in history,please notice this new situation "
                            f"the trade strategy is {pre_trade_strategy}\n")
                      
            elif action is None:
                print(f'Still waiting for a chance, signal: {trade_signal}, trade strategy: {trade_strategy}')
                with open(log_file_path, "a") as f:
                    f.write(f"Order time: {order_time.strftime('%Y-%m-%d %H')},"
                            f"Still waiting for a chance, signal: {trade_signal}, trade strategy: {trade_strategy}\n")
            else:
                print(f'Still waiting for the price to make order, action_time:{action_time},signal: {trade_signal}, trade strategy: {trade_strategy}')
                with open(log_file_path, "a") as f:
                    f.write(f"Still waiting for the price to make order, action_time:{action_time}, "
                            f"signal: {trade_signal}, trade strategy: {trade_strategy}\n")
            
            make_order.to_csv(file_path, index=False)
        elif last_order_date == tick_date:
            trade_strategy = 0
            make_order['strategy'] = 0
            make_order['trade_signal'] = None
            make_order.to_csv(file_path, index=False)
            print(f'The order was already made at order time: {last_order_date}. No duplicate orders at the same time allowed.')
            with open(log_file_path, "a") as f:
                f.write(f"The order was already made at order time: {last_order_date}. "
                        f"No duplicate orders at the same time allowed.\n")
        else:
            print(f'No trade chance for this symbol -- {symbol}. '
                  f'Last close price: {record.close}, upper band: {record.ub}, lower band: {record.lb}, '
                  f'hour: {record.hour}, RSI: {record.rsi}, RSI signal: {record.signal}')
        
        time.sleep(5)

    except Exception as e:
        # Log the exception with traceback
        print("An error occurred! Restarting...")
        print(traceback.format_exc())
        time.sleep(5)  # Optional delay before retrying



