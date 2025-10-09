import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
import pandas_ta as ta
import talib as ta1
from common import login,password,server
from common import login_real,password_real,server_real

# login=23000437
# password='7$YC8qt&1fr&Lh'
# server='ICMarketsAU-Demo'


mt.initialize()
# mt.login(login,password,server)
mt.login(login_real,password_real,server_real)

# disk='C:/c/'
disk='E:/'

version='2.63_2_real'
currency='EURAUD'

def get_previous_rows(df, condition_col, condition_val, n):
    """
    Extract the previous `n` rows from a DataFrame when a condition is met.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        condition_col (str): Column name to check condition
        condition_val (any): Value that triggers the condition (default=1)
        n (int): Number of previous rows to collect
    
    Returns:
        pd.DataFrame: All previous rows stacked into one dataframe
    """
    all_prev_rows = []
    indices = df.index[df[condition_col] == condition_val].tolist()
    
    for idx in indices:
        if idx >= n:
            end = idx+1
            prev_rows = df.iloc[idx-n:end].copy()
            prev_rows["signal_index"] = idx  # Tag which signal triggered
            all_prev_rows.append(prev_rows)
    
    if all_prev_rows:
        return pd.concat(all_prev_rows, ignore_index=True)
    else:
        return pd.DataFrame()  # empty if no matches


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
            sl=order_price+0.006*order_price
    elif trade_signal=='buy':
        if data.sd>0.01:
            tp=order_price+0.01*order_price  
            sl=order_price-0.01*order_price
        elif data.sd>0.009:
            tp=order_price+0.007*order_price  
            sl=order_price-0.008*order_price
        else:
            tp=order_price+0.005*order_price  
            sl=order_price-0.006*order_price
    return tp,sl


def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=30
    return data

def macd(df, short_window=12, long_window=26, signal_window=9, ema_period=200):
    # MACD
    df['ShortEMA'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['LongEMA'] = df['close'].ewm(span=long_window, adjust=False).mean()
    df['MACD'] = df['ShortEMA'] - df['LongEMA']
    df['Ema_Signal'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    # EMA200 trend filter
    df['EMA200'] = df['close'].ewm(span=ema_period, adjust=False).mean()
    
    # Generate signals
    signals = []
    for i in range(1, len(df)):
        # Buy Signal: MACD crosses above Signal & price above EMA200
        if df['MACD'][i] > df['Ema_Signal'][i] and df['MACD'][i-1] <= df['Ema_Signal'][i-1]:
            if df['close'][i] > df['EMA200'][i]:
                signals.append('Buy')
            else:
                signals.append('')
        # Sell Signal: MACD crosses below Signal & price below EMA200
        elif df['MACD'][i] < df['Ema_Signal'][i] and df['MACD'][i-1] >= df['Ema_Signal'][i-1]:
            if df['close'][i] < df['EMA200'][i]:
                signals.append('Sell')
            else:
                signals.append('')
        else:
            signals.append('')
    signals.insert(0,'')  # No signal for first candle
    df['Signal_Strategy'] = signals
    return df



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

class position:
    def __init__(self,open_datetime,open_price,order_type,volume,sl,tp,symbol,is_trade,sd):
        self.open_datetime=open_datetime
        self.open_price=open_price
        self.order_type=order_type
        self.volume=volume
        self.sl=sl
        self.tp=tp
        self.close_datetime=None
        self.close_price=None
        self.profit=0
        self.status='open'
        self.symbol=symbol
        self.is_trade=is_trade
        self.sd=sd

    def close_position(self,close_date_time,close_price,status):
        self.close_datetime=close_date_time
        self.close_price=close_price
        self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status=status

    def modify_poistion(self,tp,sl):
        self.tp=tp
        self.sl=sl
    
    def _asdict(self):
        return {
            'open_datetime':self.open_datetime,
            'open_price':self.open_price,
            'order_type':self.order_type,
            'volume': self.volume,
            'sl':self.sl,
            'tp':self.tp,
            'close_datetime':self.close_datetime,
            'close_price':self.close_price,
            'profit':self.profit,
            'status':self.status,
            'symbol':self.symbol,
            'is_trade':self.is_trade,
            'sd':self.sd
        }

class Strategy:

    def __init__(self,df,starting_balance,volume):
        self.starting_balance=starting_balance
        self.volume=volume
        self.positions=[]
        self.data=df
    
    def get_positions_df(self):
        df=pd.DataFrame([position._asdict() for position in self.positions])
        if not df.empty:
            df['pnl_close']=df['profit'].cumsum()+self.starting_balance
        else: df['pnl_close']=self.starting_balance
        return df
    
    def get_equity_df(self):
        df=pd.DataFrame([position._asdict() for position in self.positions])
        df['pnl_equity']=df['profit'].cumsum()+self.starting_balance
        return df
    
    def add_position(self,position):
        self.positions.append(position)

    def trading_allowed(self):
        i=0
        for pos in self.positions:
            if pos.status=='open':
                i=i+1
        if  i>=10:
            return False
        else:
            return True
    
    def run(self,trade):
        # self.data.
            is_trade=0
            trade_signal=None
            track_order=0
            pre_row=pd.DataFrame()
            for i, data in df.iterrows():
                
              if i>1:
                pre_row=df.iloc[i-1]
                pre_2_row=df.iloc[i-2]
                pre_3_row=df.iloc[i-3]
                
                if i<len(df)-1:
                    next_row=df.iloc[i + 1]
                    if not pre_row.empty :
                        if is_trade==0  and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1 and data.buy_cnt==0 and data.lower_30==0:
                            is_trade=1.1
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1\
                                and data.buy_cnt==0 and data.lower_30==2:
                            is_trade=1.2
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30==1  \
                                and data.buy_cnt==2:
                            is_trade=1.3
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2  \
                                and data.buy_cnt==0 and data.lower_30==0:
                            is_trade=1.4
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>=2  \
                                and data.buy_cnt==0 and  data.lower_30>0:
                            is_trade=1.5
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='buy' and pre_row.buy_cnt==1 and pre_row.lower_30>1  \
                                and data.buy_cnt==2:
                            is_trade=1.6
                            trade_signal='buy'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.rsi>30 and pre_row.rsi<32 and data.rsi>32 and pre_row.close<pre_row.lb:
                            is_trade=1.7
                            trade_signal='buy'
                        elif is_trade==0  and track_order<=10 \
                                and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 and data.sell_cnt==0  and data.over_70==0:
                            is_trade=2.1
                            trade_signal='sell'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1 \
                                and data.sell_cnt==0 and data.over_70==2:
                            is_trade=2.2
                            trade_signal='sell'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70==1  \
                                and data.sell_cnt==2:
                            # print(data.time)
                            is_trade=2.3
                            trade_signal='sell'
                        elif is_trade==0  and  track_order<=10\
                                and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70>1  \
                                and data.sell_cnt==2:
                            is_trade=2.4
                            trade_signal='sell'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.signal=='sell' and pre_row.sell_cnt==1 and pre_row.over_70>1 \
                                and data.sell_cnt==0:
                            is_trade=2.5
                            trade_signal='sell'
                        elif is_trade==0 and track_order<=10\
                                and pre_row.rsi>68 and pre_row.rsi<70 and data.rsi<68 and pre_row.close>pre_row.ub:
                            is_trade=2.6
                            trade_signal='sell'
                    if trade==True:
                        # print(is_trade)
                        if is_trade==1.1 and self.trading_allowed():
                            if pre_row.low_rsi>max(pre_row.high_rsi,pre_row.rsi) and data.low_rsi<max(data.rsi,data.high_rsi):
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.111      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi>max(pre_row.high_rsi,pre_row.rsi) and data.low_rsi>max(data.rsi,data.high_rsi)\
                                and pre_2_row.low_rsi>max(pre_2_row.high_rsi,pre_2_row.rsi):
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.112      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0                                
                            elif pre_row.low_rsi>max(pre_row.high_rsi,pre_row.rsi):
                                is_trade=3.11
                                trade_signal='sell'
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi) and pre_row.high_rsi<max(pre_row.low_rsi,pre_row.rsi)\
                                and data.high_rsi<pre_row.high_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.121    
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0 
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi) and data.low_rsi<pre_row.low_rsi and data.sd>0.004:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.122      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0 
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi) and (data.low_rsi-pre_row.low_rsi)/data.low_rsi>0.000001 \
                                and data.high_rsi>pre_row.high_rsi and data.sd>0.004:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.123      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi):
                                is_trade=3.12
                                trade_signal='sell'
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.rsi<min(pre_row.high_rsi,pre_row.low_rsi) and data.high_rsi>data.low_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.1311      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.rsi<min(pre_row.high_rsi,pre_row.low_rsi) and data.high_rsi<data.low_rsi\
                                and data.low_rsi>pre_row.low_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.1312      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_row.rsi<min(pre_row.high_rsi,pre_row.low_rsi):
                                    is_trade=3.13
                                    trade_signal='sell'                              
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_2_row.rsi>min(pre_2_row.high_rsi,pre_2_row.low_rsi) \
                                and data.high_rsi>pre_row.high_rsi and pre_2_row.high_rsi<pre_2_row.low_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.132      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0 
                            elif pre_row.Signal_Strategy!='Sell' and pre_2_row.Signal_Strategy!='Sell' and pre_3_row.Signal_Strategy!='Sell'\
                                and pre_2_row.rsi>min(pre_2_row.high_rsi,pre_2_row.low_rsi):
                                is_trade=3.14
                                trade_signal='sell'
                            elif pre_row.Signal_Strategy=='Sell' or pre_2_row.Signal_Strategy=='Sell' or pre_3_row.Signal_Strategy=='Sell':
                                is_trade=3.15
                                trade_signal='sell'
                        elif is_trade==1.2 and self.trading_allowed():
                            order_price=data.close
                            if data.lower_30==0 and pre_row.lower_30==2 \
                                and data.low_rsi<pre_row.low_rsi:
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.21      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.lower_30==0 and pre_row.lower_30==2:
                                is_trade=3.21
                                trade_signal='sell'
                            elif data.lower_30==0 and pre_row.lower_30>2\
                                and data.high_rsi>data.low_rsi:
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.22     
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.lower_30==0 and pre_row.lower_30>2:
                                is_trade=3.22
                                trade_signal='sell'
                        elif is_trade==1.3 and self.trading_allowed():
                            order_price=data.close
                            if data.buy_cnt==0 and pre_row.buy_cnt==2 and data.high_rsi<data.rsi \
                                and data.low_rsi<max(data.high_rsi,data.rsi) and data.low_rsi<pre_row.low_rsi:
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.311      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.high_rsi<data.rsi \
                                and data.low_rsi>max(data.high_rsi,data.rsi) and data.low_rsi>pre_row.low_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.312      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.high_rsi<data.rsi:
                                    is_trade=3.31
                                    trade_signal='sell'
                            elif data.buy_cnt==0 and pre_row.buy_cnt==2 and pre_row.rsi>pre_2_row.rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.313      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and pre_row.buy_cnt==2 and data.high_rsi>data.rsi:
                                    is_trade=3.32
                                    trade_signal='sell'
                            elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.high_rsi<data.rsi:
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.321      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and pre_row.buy_cnt==3 and data.high_rsi>max(data.rsi,data.low_rsi):
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.322      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and pre_row.buy_cnt==3:
                                is_trade=3.33
                                trade_signal='sell'
                            elif data.buy_cnt==0 and data.high_rsi>pre_row.high_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.331      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.buy_cnt==0 and data.high_rsi<pre_row.high_rsi and data.low_rsi<pre_row.low_rsi:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.332      
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif  data.buy_cnt==0:
                                is_trade=3.34
                                trade_signal='sell'
                        elif is_trade==1.4 and self.trading_allowed():
                                is_trade=3.4
                                trade_signal='sell' 
                        elif is_trade==1.5 and self.trading_allowed():
                            order_price=data.close
                            if pre_row.lower_30>0 and data.lower_30==0 and data.high_rsi>30:
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.5     
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.lower_30>0 and data.lower_30==0:
                                is_trade=3.5
                                trade_signal='sell'
                        elif  is_trade==1.6 and self.trading_allowed():
                            if pre_row.buy_cnt>0 and data.buy_cnt==0 and data.lower_30==0:
                                is_trade=3.61
                                trade_signal='sell'
                            elif pre_row.buy_cnt>0 and data.buy_cnt==0 and data.lower_30>0:
                                is_trade=1.62
                        elif is_trade==1.62 and self.trading_allowed():
                            if  pre_row.lower_30>0 and data.lower_30==0 and pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi)\
                                and pre_row.high_point!=1:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.62
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.lower_30>0 and data.lower_30==0:
                                is_trade=3.62
                                trade_signal='sell'
                        elif is_trade==1.7 and self.trading_allowed():
                            if data.high_rsi>data.low_rsi and pre_row.low_rsi<max(pre_row.rsi,pre_row.high_rsi)\
                                and data.lower_30_low!=2:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.71   
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.high_rsi>data.low_rsi:
                                is_trade=3.71
                                trade_signal='sell'
                            elif data.lower_30_high>0 and data.sd>0.004:
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.721   
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.lower_30_high==0 and data.low_rsi>max(data.rsi,data.high_rsi):
                                order_price=data.close
                                if next_row.low<=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=1.722   
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            else:
                                is_trade=3.72
                                trade_signal='sell'
                        elif is_trade==2.1 and self.trading_allowed():
                            if pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.rsi\
                                and data.high_rsi<pre_row.high_rsi and pre_2_row.low_point!=1:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.111
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.rsi\
                                and data.high_rsi<pre_row.high_rsi and pre_2_row.low_point==1 and pre_row.high_point==1:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.112
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.rsi\
                                and data.high_rsi>pre_row.high_rsi and data.over_70_high<3:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.113
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif  pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi<pre_row.rsi:
                                is_trade=4.11
                                trade_signal='buy' 
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi>pre_row.rsi\
                                and data.high_rsi>pre_row.high_rsi and pre_2_row.rsi>pre_2_row.high_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.114
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi>pre_row.rsi\
                                and data.high_rsi<pre_row.high_rsi and pre_2_row.low_rsi<pre_2_row.high_rsi and pre_row.low_rsi>70:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.115
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi>pre_row.rsi\
                                and data.high_rsi<pre_row.high_rsi and pre_2_row.low_rsi<pre_2_row.high_rsi and pre_row.low_rsi<70\
                                and pre_2_row.low_point==1:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.116
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi) and pre_row.high_rsi>pre_row.rsi\
                                and data.high_rsi<pre_row.high_rsi and pre_2_row.low_rsi>pre_2_row.high_rsi \
                                and pre_row.high_rsi>data.low_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.117
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0                                   
                            elif  pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi):
                                is_trade=4.12
                                trade_signal='buy'
                            elif data.low_rsi>max(data.rsi,data.high_rsi) and pre_row.low_rsi>max(pre_row.rsi,pre_row.high_rsi)\
                                and data.low_rsi<76 and pre_row.low_rsi<76 :
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.118
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif data.low_rsi<max(data.rsi,data.high_rsi) and pre_2_row.low_rsi>max(pre_2_row.rsi,pre_2_row.high_rsi):
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.119
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0 
                            else:
                                is_trade=4.13
                                trade_signal='buy'
                        elif is_trade==2.2 and self.trading_allowed():
                            if  pre_row.over_70>0 and data.over_70==0\
                                and pre_row.high_rsi<pre_row.low_rsi and data.over_70_high!=2: 
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.21
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0 
                            elif pre_row.over_70>0 and data.over_70==0\
                                and  pre_row.high_rsi>pre_row.low_rsi and pre_2_row.high_rsi<min(pre_2_row.rsi,pre_2_row.low_rsi)\
                                and pre_row.high_rsi>pre_2_row.high_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.22
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif  pre_row.over_70>0 and data.over_70==0:
                                is_trade=4.2
                                trade_signal='buy' 
                        elif is_trade==2.3 and self.trading_allowed():
                            if  pre_row.sell_cnt==2 and data.sell_cnt==0 and data.low_rsi<data.high_rsi\
                                and data.low_rsi<70 and pre_row.low_rsi<min(pre_row.rsi,pre_row.high_rsi):
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.311
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.low_rsi<data.high_rsi\
                                and data.low_rsi>70 and data.over_70_high!=4:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.312
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.low_rsi<data.high_rsi:
                                is_trade=4.311
                                trade_signal='buy'
                            elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.low_rsi>data.high_rsi\
                                and pre_2_row.low_point==1 and pre_2_row.rsi<pre_2_row.low_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.313
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt==2 and data.sell_cnt==0 and data.low_rsi>data.high_rsi\
                                and data.low_rsi>data.high_rsi and pre_row.low_rsi>pre_row.high_rsi and pre_2_row.low_rsi>pre_2_row.high_rsi\
                                and data.low_rsi>pre_row.low_rsi and data.high_rsi<pre_row.high_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.314
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt==2 and data.sell_cnt==0:
                                is_trade=4.312
                                trade_signal='buy'
                            elif pre_row.sell_cnt>2 and data.sell_cnt==0\
                                and pre_2_row.low_rsi>max(pre_2_row.rsi,pre_2_row.high_rsi) and pre_row.low_rsi>pre_2_row.low_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    if data.sd<0.01:
                                        tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    else:
                                        tp=order_price-0.009*order_price  
                                        sl=order_price+0.01*order_price
                                    is_trade=2.321
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                            elif pre_row.sell_cnt>2 and data.sell_cnt==0\
                                and pre_2_row.low_rsi>max(pre_2_row.rsi,pre_2_row.high_rsi):
                                is_trade=4.321
                                trade_signal='buy'
                            elif pre_row.sell_cnt>2 and data.sell_cnt==0\
                                and data.low_rsi<70 and pre_row.rsi>pre_row.low_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    if data.sd<0.01:
                                        tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    else:
                                        tp=order_price-0.009*order_price  
                                        sl=order_price+0.01*order_price
                                    is_trade=2.322
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt>2 and data.sell_cnt==0\
                                and data.low_rsi>70 and pre_row.rsi<pre_row.low_rsi and pre_row.low_rsi<pre_row.high_rsi:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    if data.sd<0.01:
                                        tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    else:
                                        tp=order_price-0.009*order_price  
                                        sl=order_price+0.01*order_price
                                    is_trade=2.323
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt>2 and data.sell_cnt==0:
                                is_trade=4.322
                                trade_signal='buy'
                        elif is_trade==2.4 and self.trading_allowed(): 
                            if pre_row.sell_cnt>0 and data.sell_cnt==0\
                                and data.rsi<80 and pre_row.low_rsi<max(pre_row.high_rsi,pre_row.rsi):
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.41
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.sell_cnt>0 and data.sell_cnt==0\
                                and data.rsi<80 and  pre_row.low_rsi>max(pre_row.high_rsi,pre_row.rsi)\
                                and pre_row.rsi>min(pre_row.low_rsi,pre_row.high_rsi):
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.42
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif  pre_row.sell_cnt>0 and data.sell_cnt==0:
                                is_trade=4.4
                                trade_signal='buy'
                        elif is_trade==2.5 and self.trading_allowed():
                            if pre_row.over_70>0 and data.over_70==0\
                                and pre_row.low_point==1:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.5
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.over_70>0 and data.over_70==0:
                                is_trade=4.5
                                trade_signal='buy'
                        elif is_trade==2.6 and self.trading_allowed():
                            if pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi)\
                                and pre_2_row.low_rsi<min(pre_2_row.high_rsi,pre_2_row.rsi)\
                                and pre_row.low_rsi>=60 and pre_row.low_rsi>min(data.low_rsi,pre_2_row.low_rsi):
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.61
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi)\
                                and pre_2_row.low_rsi>max(pre_2_row.high_rsi,pre_2_row.rsi)\
                                and pre_2_row.low_rsi<70:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.62
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_row.low_rsi<min(pre_row.high_rsi,pre_row.rsi):
                                is_trade=4.61
                                trade_signal='buy'
                            elif pre_2_row.low_rsi>70 and pre_2_row.over_70_low>pre_2_row.over_70_high:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.63
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            elif pre_2_row.low_rsi<70 and data.Signal_Strategy!='Buy' \
                                and pre_row.Signal_Strategy!='Buy' and pre_2_row.Signal_Strategy!='Buy'\
                                and pre_2_row.low_rsi>60:
                                order_price=data.close 
                                if next_row.high>=order_price:
                                    tp,sl=set_profit_loss(data,order_price,trade_signal)
                                    is_trade=2.64
                                    self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,data.sd))
                                    track_order=track_order+1
                                    is_trade=0
                                else: is_trade=0
                            else:
                                is_trade=4.62
                                trade_signal='buy'
                        elif is_trade==3.11 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==3.12 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==3.13 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==3.14 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.15 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.21 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==3.22 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.31 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0  
                        elif is_trade==3.32 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.33 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.34 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.4 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.5 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==3.61 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.62 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.71 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==3.72 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.high>=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.11 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.12 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.13 and self.trading_allowed():
                            print(data.time)
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.2 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.311 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.312 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.321 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0 
                        elif is_trade==4.322 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                if pre_row.sd<0.01:
                                    tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                else:
                                    tp=order_price+0.009*order_price  
                                    sl=order_price-0.01*order_price
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.4 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.5 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.61 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0
                        elif is_trade==4.62 and self.trading_allowed():
                            order_price=pre_row.close
                            if data.low<=order_price:
                                tp,sl=set_profit_loss(pre_row,order_price,trade_signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade,pre_row.sd))
                                track_order=track_order+1
                                is_trade=0
                            else: is_trade=0                                                
                        else:
                            is_trade=0       
                    for idx, pos in enumerate(self.positions):
                        if pos.status=='open' and data.time>=pos.open_datetime:       
                            df123=self.get_positions_df()
                            # print(df123)
                            if not df123.empty:
                                profit= df123['pnl_close'].iloc[-1]
                            #    print(profit)
                            if pos.order_type=='buy' :
                                total_profit=(data.low-pos.open_price)*pos.volume+profit
                            else:
                                total_profit=(pos.open_price-data.high)*pos.volume+profit
                            if total_profit<profit/2 and  pos.order_type=='buy':
                                pos.close_position(data.time,data.low,'closed')
                                is_trade=0
                                trade=False
                            elif total_profit<profit/2 and  pos.order_type=='sell':
                                pos.close_position(data.time,data.high,'closed')
                                is_trade=0
                                trade=False
                            elif (pos.sl>=data.low and pos.order_type=='buy'):
                                pos.close_position(data.time,pos.sl,'closed')
                                track_order=track_order-1
                            elif (pos.sl<=data.high and pos.order_type=='sell'):
                                pos.close_position(data.time,pos.sl,'closed')
                                track_order=track_order-1
                            elif (pos.tp<=data.high and pos.order_type=='buy'):
                                pos.close_position(data.time,pos.tp,'closed')
                                track_order=track_order-1
                            elif (pos.tp>=data.low and pos.order_type=='sell'):
                                pos.close_position(data.time,pos.tp,'closed')
                                track_order=track_order-1
                            elif pos.order_type=='buy':
                                pos.close_position(data.time,data.close,'open')
                            elif pos.order_type=='sell':
                                pos.close_position(data.time,data.close,'open')
            return self.get_positions_df()

df1=pd.DataFrame()
df2=pd.DataFrame()
j=0
volumes = list(range(1000, 1000 + 1000, 1000))
years=list(range(2025, 2025 + 1, 1))
print(years)
# symbol=['GBPNZD','GBPCAD','NZDCAD','GBPAUD','GBPUSD']

symbol=[f'{currency}']
# years=[2024]
# volumes=[10000]

# aa=a.iloc[40:]



# symbols=mt.symbols_get()
# df3=pd.DataFrame(symbols)
# a=df3.iloc[:,[93,95]]
# a.reset_index(inplace=True)
# # a.to_csv('E:/EA/bollinger-bands/all_main_sybol.csv')
# b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
# c=b[(~a.iloc[:,1].str.contains('.a'))]

# symbol=c.iloc[:,1]


df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol','is_trade'])

for year in years:
    print(year)
    for currency in symbol:
        print(f'{currency}--start')
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year-7,1,1), datetime(year,12,31))
      
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour
        

        df['sma']=df['close'].rolling(20).mean()
        df['sd']=df['close'].rolling(20).std()
        df['lb']=df['sma']-2*df['sd']
        df['ub']=df['sma']+2*df['sd']
        
        df=find_lower_high_point(df,'tick_volume')
        df = macd(df)
        
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


        # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
        # fig.show()
    
        # df=rsi(df,14)
        df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'],df['rsi'],df['overbought'],df['oversold'])
        df['buy_cnt']=count_signal_buy(df,'signal')
        df['sell_cnt']=count_signal_sell(df, 'signal')
        df.reset_index(inplace=True)
        # df.to_csv(f'E:/EA/bollinger-bands/H4_year/b_{year}_opi_8.5.csv')
        # df.to_csv(f'C:/c/EA/bollinger-bands/H4_year/b_{year}_opi_8.5.csv')
        # df_h1.to_csv(f'C:/c/EA/bollinger-bands/H4_year/b_h1_{year}.csv')
        # df.to_csv('C:/Ally/a.csv')
        print(f'{currency} have been got and start run the strategy')
        for volume in volumes:
            print(volume)
            bollinger_strategy=Strategy(df,200,volume)
            trade=True
            result=bollinger_strategy.run(trade)
            open_rows = result[result['status'] == 'open']
            if not open_rows.empty:
                print(open_rows)
            last=result[-1:]
            df1=pd.concat([df1,result])
            df2=pd.concat([df2,last])
            j=j+1
            print(f'{currency} have finished-{j}')
        df=df.merge(df1,how='left',left_on=['time'],right_on=['open_datetime'])
        df_extract=get_previous_rows(df, condition_col="is_trade", condition_val=2.63, n=3)
        df.to_csv(f'{disk}/EA/bollinger-bands/H4_year/{currency}/b_{year}_opi_result_{version}.csv',index=False)
        df_extract.to_csv(f'{disk}/EA/bollinger-bands/H4_year/{currency}/b_{year}_opi_result_extract_{version}.csv',index=False)
        # df.to_csv(f'E:/EA/bollinger-bands/H4_year/b_{year}_opi_result_8.5.csv',index=False)

current_time = datetime.now()
df1['win_rate']=np.where(df1['profit']<0,0,1)
df1['close_datetime'] = df1['close_datetime'].fillna(current_time)
df1['year']=df1['close_datetime'].dt.year
df1['profit_rate'] = np.where(
    df1['profit'] > 0,
    abs(df1['tp'] - df1['open_price']) / df1['open_price'],
    -(abs(df1['sl'] - df1['open_price']) / df1['open_price'])
)

# Convert datetime columns to pandas Timestamps
df1['open_datetime'] = pd.to_datetime(df1['open_datetime'])
df1['close_datetime'] = pd.to_datetime(df1['close_datetime'])

# Now subtract them
df1['date_diff'] = (df1['close_datetime'] - df1['open_datetime']).dt.days


win_result=df1.groupby(['year','win_rate','volume']).agg({'open_datetime':"count"}).reset_index()
pivot_table = win_result.pivot_table(index=['year','win_rate'], columns='volume', values='open_datetime')
# col_sums = win_result['open_datetime'].sum()
# win_result['win']=win_result['open_datetime'].div(col_sums,axis=0)
df2['close_datetime'] = df2['close_datetime'].fillna(current_time)
df2['year']=df2['close_datetime'].dt.year
revenue_result=df2.groupby(['year','volume']).agg({'pnl_close':"sum"})
revenue_result = revenue_result.unstack()


print(pivot_table)

print(revenue_result)
    
df1.to_csv(f'{disk}EA/bollinger-bands/H4_year/{currency}/result_detail_volumn_rsi_opi_{version}.csv')
df2.to_csv(f'{disk}EA/bollinger-bands/H4_year/{currency}/final_result_volumn_detail_rsi_opi_{version}.csv')

# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_opiti_8.5.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_opiti_8.5.csv')
# 'E:/EA/bollinger-bands/H1_year'
print('finish')
    # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
    # for i,position in result.iterrows():
    #     if position.status=='closed':
    #         fig.add_shape(type='line',x0=position.open_datetime,y0=position.open_price,x1=position.close_datetime,y1=position.close_price)
    #         line=dict(
    #             color='green' if position.profit>=0 else "dark",
    #             width=3
    #         )
    # fig.show()



