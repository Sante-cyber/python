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
import talib as ta1
# import datetime
import pytz

# login=51658107
# password='VxBvOa*4'
# server='ICMarkets-Demo'

def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=29
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

    if is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and (pre_row.rsi+pre_row.low_rsi)/2<30 and pre_row.high_rsi>30 \
            and data.buy_cnt==0 and data.lower_30==0 and  data.high_rsi<30 and data.high_rsi<data.low_rsi and data.sd<0.02:
        is_trade=1.1
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and (pre_row.rsi+pre_row.low_rsi)/2<30 and pre_row.high_rsi>30 \
            and data.buy_cnt==0 and data.lower_30==0 and  data.high_rsi>30 and data.sd<0.02:
        is_trade=1.2
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and (pre_row.rsi+pre_row.low_rsi)/2<30 and pre_row.high_rsi<30 \
            and data.buy_cnt==0 and data.lower_30==0 and data.high_rsi>data.low_rsi and data.sd<0.02:
        is_trade=1.3
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and (pre_row.rsi+pre_row.low_rsi)/2<30 \
            and data.buy_cnt==0 and data.lower_30==2:
        is_trade=1.4
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2 and (pre_row.rsi+pre_row.low_rsi)/2<30 \
            and data.buy_cnt==0 and data.lower_30==0 and data.sd<0.02:
        is_trade=1.6
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2  \
            and data.buy_cnt==0 and  data.lower_30>0:
        is_trade=1.7
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1  \
            and data.buy_cnt==2:
        is_trade=1.5
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>1  \
            and data.buy_cnt==2:
        is_trade=1.8
        trade_signal='buy'
    elif is_trade==0 \
            and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 and (pre_row.rsi+pre_row.low_rsi)/2>70 and pre_row.high_rsi>70 and (pre_row.high_point>0 or pre_row.low_point>0)\
            and data.sell_cnt==0  and data.over_70==0 and data.low_rsi>69 and data.high_rsi>70 and data.sd<0.02:
        is_trade=2.1
        trade_signal='sell'
    elif is_trade==0 \
            and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 and (pre_row.rsi+pre_row.low_rsi)/2>70 and pre_row.high_rsi<70\
            and data.sell_cnt==0  and data.over_70==0 and data.high_rsi<data.low_rsi:
        is_trade=2.2
        trade_signal='sell'
    elif is_trade==0 \
            and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 and (pre_row.rsi+pre_row.low_rsi)/2>70 \
            and data.sell_cnt==0 and data.over_70==2:
        is_trade=2.3
        trade_signal='sell'
    elif is_trade==0 \
            and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1  \
            and data.sell_cnt==2:
        is_trade=2.4
        trade_signal='sell'
    elif is_trade==0 \
            and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70>1  \
            and data.sell_cnt==2:
        is_trade=2.5
        trade_signal='sell'
    # record=data[['time','close','sma','sd','lb','ub','high_point','low_point','rsi','signal','low_rsi','high_rsi','over_70_high','over_70_low','over_70','lower_30_high','lower_30_low','lower_30','buy_cnt','sell_cnt']]
    # pre_record=pre_row[['time','close','sma','sd','lb','ub','high_point','low_point','rsi','signal','low_rsi','high_rsi','over_70_high','over_70_low','over_70','lower_30_high','lower_30_low','lower_30','buy_cnt','sell_cnt']]
    return trade_signal,is_trade,data,pre_row,pre_2_row

def run_strategy(is_trade,signal,data,pre_row,pre_2_row,VOLUME,track_point):
    
    tick=mt.symbol_info_tick(symbol) 
    
    print(f'cuurently_bid_price_tick--{tick.ask}--last_close--{data.close}--signal--{signal}--strategy--{is_trade}--sd')
    
    if (is_trade==1.1 or is_trade==1.3):
        order_price=data.close
        if tick.ask<=order_price:
            order_price=tick.ask
            sl=order_price-2*data.sd
            tp=order_price+2*data.sd
            if (tp-order_price)/order_price>0.0058:
                tp=order_price+0.0058*order_price
            if (order_price-sl)/order_price>0.0058:
                sl=order_price-0.0058*order_price       
            result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
            is_trade=0
        else: is_trade=0
    elif is_trade==1.2:
        order_price=data.close
        if tick.ask<=order_price:
            order_price=tick.ask
            sl=order_price-2*data.sd
            tp=order_price+2*data.sd
            if (tp-order_price)/order_price>0.005:
                tp=order_price+0.005*order_price
            if (order_price-sl)/order_price>0.0058:
                sl=order_price-0.0058*order_price       
            result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
            is_trade=0
        else: is_trade=0
    elif is_trade==1.4:
        # elif data.buy_cnt==0 and pre_row.buy_cnt==0 and (pre_row.rsi+pre_row.low_rsi)/2<30 and data.lower_30!=0: 
        if pre_row.lower_30>2 and pre_row.lower_30<=3 and data.lower_30==0 and abs((data.close-data.open)/data.close)<0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd
                if (tp-order_price)/order_price>0.0058:
                    tp=order_price+0.0058*order_price  
                if (order_price-sl)/order_price>0.0058:
                    sl=order_price-0.0058*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        if data.lower_30==0 and pre_2_row.lower_30>=2 and pre_2_row.lower_30<=3 and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd
                if (tp-order_price)/order_price>0.0058:
                    tp=order_price+0.0058*order_price  
                if (order_price-sl)/order_price>0.0058:
                    sl=order_price-0.0058*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif data.lower_30==0 and pre_2_row.lower_30>=5 and pre_row.lower_30==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-0.005*order_price 
                tp=order_price+0.01*order_price
                is_trade=1.41
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0  
        elif data.lower_30==0 and pre_2_row.lower_30>=2 and pre_row.lower_30==0:
                is_trade=0   
    elif is_trade==1.5 :
        # elif data.buy_cnt==0 and pre_row.buy_cnt==0 and (pre_row.rsi+pre_row.low_rsi)/2<30 and data.lower_30!=0: 
        if  pre_row.buy_cnt==2 and data.buy_cnt==0 \
            and data.lower_30==0 and data.high_rsi<data.low_rsi:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd
                if (tp-order_price)/order_price>0.0058:
                    tp=order_price+0.0058*order_price  
                if (order_price-sl)/order_price>0.0058:
                    sl=order_price-0.0058*order_price 
                is_trade=1.511
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif  data.buy_cnt==0 and pre_2_row.buy_cnt==2 and pre_row.buy_cnt==0 \
            and pre_row.lower_30==0 and pre_row.low_point!=1:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd
                if (tp-order_price)/order_price>0.0045:
                    tp=order_price+0.0045*order_price  
                if (order_price-sl)/order_price>0.0045:
                    sl=order_price-0.0045*order_price 
                is_trade=1.512
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif data.buy_cnt==0 and pre_2_row.buy_cnt==3 and pre_row.buy_cnt==0 \
                and pre_row.lower_30==0 and pre_row.low_point!=1 and pre_row.high_point==1:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                if pre_row.sd>0.01:
                    tp=order_price+3*data.sd
                else: tp=order_price+2*data.sd
                # if (tp-order_price)/order_price>0.0058:
                #     tp=order_price+0.0058*order_price  
                if (order_price-sl)/order_price>0.0058:
                    sl=order_price-0.0058*order_price  
                is_trade=1.52
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif  pre_row.buy_cnt>3 and data.buy_cnt==0 and data.lower_30==0:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                if data.marubozu==0: 
                    tp=order_price+0.005*order_price
                else: tp=order_price+3*data.sd
                # if (tp-order_price)/order_price>0.0058 and tp!=5:
                #     tp=order_price+0.0058*order_price  
                # if (order_price-sl)/order_price>0.0058:
                #     sl=order_price-0.0058*order_price  
                is_trade=1.53
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif  pre_row.buy_cnt<=3 and pre_row.buy_cnt>0  and pre_row.lower_30>0 and pre_row.lower_30_high>0 and pre_row.lower_30>pre_row.lower_30_high and pre_row.lower_30==pre_row.lower_30_low  and\
                data.buy_cnt==0 and data.lower_30==data.lower_30_low and data.lower_30>data.lower_30_high and data.lower_30>0 and data.lower_30_high>0: 
                order_price=data.close
                if tick.ask.low<=order_price:
                    order_price=tick.ask
                    sl=order_price-2*data.sd
                    tp=order_price+2*data.sd  
                    if (tp-order_price)/order_price>0.009:
                        tp=order_price+0.009*order_price  
                    if (order_price-sl)/order_price>0.0058:
                        sl=order_price-0.0058*order_price 
                    is_trade=1.54
                    result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                    is_trade=0
                else:is_trade=0
        elif  data.buy_cnt==0 and data.lower_30>0 and  pre_row.buy_cnt>=2:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
                is_trade=1.55
        elif  pre_2_row.buy_cnt>=2 and pre_row.buy_cnt==0:
                is_trade=0   
    elif is_trade==1.55:
        if pre_row.lower_30>0 and pre_row.lower_30>pre_row.lower_30_high and pre_row.lower_30_low==0 and pre_2_row.lower_30_low>0 and\
            data.lower_30_low==0 and data.lower_30_high==0 and data.buy_cnt==0 and data.lower_30==0:
            order_price=data.close
            if tick.ask.low<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd  
                is_trade=1.551
                if (tp-order_price)/order_price>0.009:
                    tp=order_price+0.009*order_price  
                if (order_price-sl)/order_price>0.0058:
                    sl=order_price-0.0058*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.lower_30>0 and pre_row.lower_30>pre_row.lower_30_high and pre_row.lower_30_low>0 and\
            data.lower_30_low>0 and data.lower_30_high==0 and data.buy_cnt==0 and data.lower_30==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd  
                is_trade=1.552
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.lower_30>0 and pre_row.lower_30==pre_row.lower_30_high and\
                data.buy_cnt==0 and data.lower_30==0 and data.lower_30_high>0:
                is_trade=1.553
        elif pre_row.lower_30>0 and pre_row.lower_30<pre_row.lower_30_high and\
                data.buy_cnt==0 and data.lower_30==0 and data.lower_30_low>0 and data.lower_30_high>0:
                is_trade=1.554     
        elif pre_row.lower_30>0 and data.lower_30==0 and data.buy_cnt==0:
                is_trade=0
    elif is_trade==1.553:
        if pre_row.lower_30_high>0 and data.lower_30_high==0 and data.buy_cnt==0 and data.lower_30==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0  
        elif pre_row.lower_30_high>0 and data.lower_30_high==0:
            is_trade=0
    elif is_trade==1.554:
        if pre_row.lower_30_low>0 and data.lower_30_low==0 and data.buy_cnt==0 and data.lower_30==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0  
        elif pre_row.lower_30_low>0 and data.lower_30_low==0:
            is_trade=0
    elif  is_trade==1.6:
        order_price=data.close
        if tick.ask<=order_price:
            order_price=tick.ask
            sl=order_price-2*data.sd
            tp=order_price+3*data.sd
            # if (tp-order_price)/order_price>0.0058:
            #     tp=order_price+0.0058*order_price
            # if (order_price-sl)/order_price>0.0058:
            #     sl=order_price-0.0058*order_price       
            result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
            is_trade=0
        else: is_trade=0 
    elif  is_trade==1.7:
        if pre_row.lower_30>0 and data.lower_30==0 and data.buy_cnt==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                if data.sd<0.02:
                        sl=order_price-2*data.sd
                        tp=order_price+2*data.sd
                else: 
                        tp=order_price+0.006*order_price
                        sl=order_price-0.006*order_price
                # if (tp-order_price)/order_price>0.006:
                #     tp=order_price+0.006*order_price
                # if (order_price-sl)/order_price>0.006:
                #     sl=order_price-0.006*order_price       
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: is_trade=0 
    elif  is_trade==1.8:
        if (pre_row.lower_30>3 and pre_row.buy_cnt>0 and data.lower_30==0 and data.buy_cnt==0)\
            or (pre_row.lower_30==3 and pre_row.buy_cnt>0 and data.low_rsi<30 and data.high_rsi<30 and data.lower_30==0 and data.buy_cnt==0):
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd
                # if (tp-order_price)/order_price>0.0058:
                #     tp=order_price+0.0058*order_price
                # if (order_price-sl)/order_price>0.0058:
                #     sl=order_price-0.0058*order_price       
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: is_trade=0 
        elif pre_row.lower_30==3 and pre_row.buy_cnt>0 and data.lower_30==0 and data.buy_cnt==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.004*order_price
                sl=order_price-0.004*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0 
        elif pre_row.lower_30==0 and pre_row.buy_cnt>0 and data.lower_30==0 and data.buy_cnt==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.004*order_price
                sl=order_price-0.004*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0 
        elif pre_row.lower_30>0 and pre_row.buy_cnt==0 and data.high_rsi<30 and data.lower_30==0 and data.buy_cnt==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                tp=order_price+0.005*order_price
                sl=order_price-0.005*order_price
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0 
        elif pre_row.lower_30>0 and pre_row.buy_cnt==0 and data.high_rsi<20:
            is_trade=1.81
        elif pre_row.lower_30>0 and pre_row.buy_cnt==0 and data.lower_30==0 and data.buy_cnt==0:
            is_trade=1.82
        elif  data.lower_30==0 and data.buy_cnt==0:
            is_trade=0    
    elif is_trade==1.81 :
        if (pre_row.lower_30>0 or pre_row.buy_cnt>0) and data.lower_30==0 and data.buy_cnt==0:
            order_price=data.close
            if tick.ask<=order_price:
                order_price=tick.ask
                sl=order_price-2*data.sd
                tp=order_price+2*data.sd  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else: is_trade=0 
    elif is_trade==1.82 :
        if track_point<=1:
            if data.low_point==1:
                track_point=track_point+1
        elif track_point==2:
            if pre_row.low_point==1:
                order_price=data.close
                if tick.ask<=order_price:
                    order_price=tick.ask
                    sl=order_price-2*data.sd
                    tp=order_price+3*data.sd  
                    result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                    is_trade=0
                    track_point=0
            else: 
                is_trade=0
                track_point=0                                                                   
    elif (is_trade==2.1 or is_trade==2.2):
        order_price=data.close
        if tick.bid>=order_price:
            order_price=tick.bid
        # print(f'{data}--{next_row}')
            if is_trade==2.1 and abs(data.low_rsi-data.high_rsi)/data.low_rsi<0.0025:
                tp=order_price-0.004*order_price 
                sl=order_price+0.004*order_price
            else:
                sl=order_price+1*data.sd
                tp=order_price-2*data.sd
                if (order_price-tp)/order_price>0.006:
                    tp=order_price-0.006*order_price  
                if (sl-order_price)/order_price>0.006:
                    sl=order_price+0.006*order_price 
            result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
            is_trade=0
        else: is_trade=0
    elif is_trade==2.3:
        # elif data.buy_cnt==0 and pre_row.buy_cnt==0 and (pre_row.rsi+pre_row.low_rsi)/2<30 and data.lower_30!=0: 
        if pre_row.over_70>=2 and pre_row.over_70<=3 and data.over_70==0 and abs((data.close-data.open)/data.close)<0.00001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                if (order_price-tp)/order_price>0.0058:
                    tp=order_price-0.0058*order_price  
                if (sl-order_price)/order_price>0.0058:
                    sl=order_price+0.0058*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        if data.over_70==0 and pre_2_row.over_70>=2 and pre_2_row.over_70<=3 and pre_row.over_70==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.00001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                if (sl-order_price)/order_price>0.005:
                    sl=order_price+0.006*order_price  
                if (order_price-tp)/order_price>0.005:
                    tp=order_price-0.005*order_price  
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.over_70>=7 and data.over_70==0:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                tp=order_price-2*data.sd
                sl=order_price+0.005*order_price 
                is_trade=2.31
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0   
        elif data.over_70==0 and pre_2_row.over_70>=2 and pre_row.over_70==0:
                is_trade=0  
    elif is_trade==2.4 :
        # elif data.buy_cnt==0 and pre_row.buy_cnt==0 and (pre_row.rsi+pre_row.low_rsi)/2<30 and data.lower_30!=0: 
        if  data.sell_cnt==0 and data.over_70_low==0 and data.over_70==0 and pre_2_row.sell_cnt==2 and pre_row.sell_cnt==0 \
            and pre_row.over_70==0 and pre_row.low_rsi<pre_row.high_rsi :
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            if pre_row.high_point!=1:
                order_price=data.close
                if tick.bid>=order_price:
                    order_price=tick.bid
                    sl=order_price+2.5*data.sd
                    tp=order_price-3*data.sd
                    # if (sl-order_price)/order_price>0.05:
                    #     sl=order_price+0.005*order_price  
                    # if (order_price-tp)/order_price>0.005:
                    #     tp=order_price-0.005*order_price 
                    is_trade=2.411
                    result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                    is_trade=0
                else:is_trade=0
            else: is_trade=0
        elif  pre_row.sell_cnt==2 and data.sell_cnt==0 \
            and data.over_70==0 and data.low_rsi>data.high_rsi and (data.over_70_high>0 or data.over_70_low>0):
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                if (sl-order_price)/order_price>0.0045:
                    sl=order_price+0.0045*order_price  
                if (order_price-tp)/order_price>0.0045:
                    tp=order_price-0.0045*order_price 
                is_trade=2.412
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif  pre_row.sell_cnt==2 and data.sell_cnt==0 and \
                data.over_70==0 and data.low_rsi>data.high_rsi and data.rsi>data.low_rsi and\
                data.over_70_high==0 and data.over_70_low==0:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.01*order_price 
                is_trade=2.413
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.sell_cnt==2 and data.sell_cnt==0 \
            and data.over_70==0 and data.low_rsi>data.high_rsi and data.rsi<data.high_rsi and\
                data.over_70_high==0 and data.over_70_low==0:
                is_trade=2.414
        elif  pre_row.sell_cnt==3 and data.sell_cnt==0 \
                and data.over_70==0 and data.low_rsi<data.high_rsi:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.0058*order_price
                tp=order_price-0.0058*order_price
                # if (tp-order_price)/order_price>0.0058:
                #     tp=order_price+0.0058*order_price  
                # if (sl-order_price)/order_price>0.0058:
                #     sl=order_price+0.0058*order_price  
                is_trade=2.42
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif  pre_row.sell_cnt>3 and data.sell_cnt==0 and  data.over_70==0:
            # and pre_row.lower_30==0 and abs((pre_row.close-pre_row.open)/pre_row.close)>=0.001:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                is_trade=2.43
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif data.sell_cnt==0 and data.over_70>0 and pre_row.sell_cnt>=2:
            is_trade=2.44
        elif  data.sell_cnt==0 and pre_2_row.sell_cnt>=2 and pre_row.sell_cnt==0:
                is_trade=0
    elif is_trade==2.414:
        if data.low_rsi>data.high_rsi and data.rsi>data.low_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.01*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif data.low_rsi<64:
            is_trade=0  
    elif is_trade==2.44:
        if pre_row.over_70>0 and data.over_70==0  and pre_row.low_rsi<70 and pre_row.high_rsi>70\
            and data.high_rsi<pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.005*order_price 
                is_trade=2.441
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        if pre_row.over_70>0 and data.over_70==0  and pre_row.low_rsi<70 and pre_row.high_rsi<70\
            and data.high_rsi<70:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.005*order_price 
                is_trade=2.442
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        # if pre_row.over_70>0 and data.over_70==0  and pre_row.low_rsi>pre_row.high_rsi and pre_row.low_rsi<70 and pre_row.high_rsi<70\
        #     and data.high_rsi<pre_row.high_rsi:
        #     order_price=data.close
        #     if next_row.high>=order_price:
        #         sl=order_price+0.005*order_price  
        #         tp=order_price-0.005*order_price 
        #         is_trade=2.442
        #         self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade))
        #         is_trade=0
        #     else:is_trade=0
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi>70  and pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<80:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.005*order_price 
                is_trade=2.443
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi>70 and  pre_row.low_rsi<80  and pre_row.high_rsi>70 and pre_row.high_rsi<80 and pre_row.low_rsi<pre_row.high_rsi\
            and data.high_rsi<pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price  
                tp=order_price-0.01*order_price 
                is_trade=2.444
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0  
        elif pre_row.over_70>0 and data.over_70==0 and pre_row.low_rsi>70 and  pre_row.low_rsi<80  and pre_row.high_rsi>70 and pre_row.low_rsi>pre_row.high_rsi:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.006*order_price  
                tp=order_price-0.007*order_price 
                is_trade=2.445
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0  
        elif pre_row.over_70>0 and data.over_70==0:
            is_trade=0                 
    elif is_trade==2.5:
        if pre_row.sell_cnt>0 and data.sell_cnt==0 and pre_row.rsi<80 and pre_row.high_rsi>80:
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                # if (sl-order_price)/order_price>0.05:
                #     sl=order_price+0.005*order_price  
                # if (order_price-tp)/order_price>0.005:
                #     tp=order_price-0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.sell_cnt>0 and data.sell_cnt==0  and pre_row.high_rsi<80 and ( pre_row.rsi>max(pre_row.high_rsi,pre_row.low_rsi) or pre_row.rsi<min(pre_row.high_rsi,pre_row.low_rsi)) :
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+0.005*order_price  
                tp=order_price-0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.sell_cnt>0 and data.sell_cnt==0 and pre_row.rsi>80 and pre_row.high_rsi>80 and pre_row.rsi<min(pre_row.high_rsi,pre_row.low_rsi):
            order_price=data.close
            if tick.bid>=order_price:
                order_price=tick.bid
                sl=order_price+2*data.sd
                tp=order_price-2*data.sd
                # if (sl-order_price)/order_price>0.05:
                #     sl=order_price+0.005*order_price  
                # if (order_price-tp)/order_price>0.005:
                #     tp=order_price-0.005*order_price 
                result=market_order(symbol,VOLUME,signal,DEVIATION,is_trade,sl,tp)
                is_trade=0
            else:is_trade=0
        elif pre_row.sell_cnt>0 and data.sell_cnt==0:
            is_trade=0   

    
    
    last_close_price=df.iloc[-1]['close']
    hour=df.iloc[-1]['hour']
    last_rsi=df.iloc[-1]['rsi']
    last_lower_band=df.iloc[-1]['lower_band']
    last_upper_band=df.iloc[-1]['upper_band']
    last_sd=df.iloc[-1]['sd']
    if last_close_price<last_lower_band and last_rsi<oversold:
        return 'buy', last_sd, last_close_price,last_upper_band,last_lower_band,hour,last_rsi
    elif last_close_price>last_upper_band and last_rsi>overbought:
        return 'sell',last_sd, last_close_price,last_upper_band,last_lower_band,hour,last_rsi
    else:
        return None,last_sd, last_close_price,last_upper_band,last_lower_band,hour,last_rsi





if mt.initialize():
    print('connect to MetaTrader5')
    # login=51658107
    # password='VxBvOa*4'
    # server='ICMarkets-Demo'
    mt.login(login_real,password_real,server_real)

    TIMEFRAME=mt.TIMEFRAME_H4
    VOLUME=0.04
    DEVIATION=5
    MAGIC=10
    SMA_PERIOD=365
    STANDARD_DEVIATIONS=2
    TP_SD=2
    SL_SD=1
    symbol='GBPAUD.a'
    signal=None
    strategy=None
    track_point=0

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
  

    print(f'Stragety symbol:{symbol}')
    
    if mt.positions_total()==0 and is_trade==0:
        symbol_df=get_realtime_data(symbol,TIMEFRAME,SMA_PERIOD)
        
        trade_signal,trade_strategy,record,pre_record,pre_2_record=get_strategy(symbol_df)
        if signal is not None:
            print(f"It's good chance to {signal} to this symbol--{symbol}")
    else:
        record,pre_record=get_strategy(symbol_df)[2:]


    if signal=='buy':
        tick=mt.symbol_info_tick(symbol) 
        print(f'cuurently_bid_price_tick--{tick.ask}--less than {last_close_price}  and rsi--{rsi} less than 28 make order')
        if tick.ask<=last_close_price:
            result=market_order(symbol,VOLUME,signal,DEVIATION,10,tick.ask-SL_SD*standard_deviation,tick.ask+TP_SD*standard_deviation)
            print(f'signal-{signal},standard_deviation--{standard_deviation}')
            print(result)
    elif signal=='sell':
        tick=mt.symbol_info_tick(symbol) 
        print(f'cuurently_bid_price_tick--{tick.bid}--bigger than {last_close_price} can make order and rsi--{rsi} bigger than 68')
        if tick.bid>=last_close_price:
            result=market_order(symbol,VOLUME,signal,DEVIATION,10,tick.bid+SL_SD*standard_deviation,tick.bid-TP_SD*standard_deviation)
            print(f'signal-{signal},standard_deviation--{standard_deviation}')
            print(result)
    else: print(f'there is no trade chance for this symbol--{symbol}--last_close_price--{last_close_price}--upper_band--{upper_band}--lower_band--{lower_band}--hour--{hour}--rsi--{rsi}')

    time.sleep(60)



