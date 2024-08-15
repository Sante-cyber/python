import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
from common import login,password,server
import pytz
import datetime as dt
import pandas_ta as ta


login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)


def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=30
    return data

def moving_average(data, window):
    data['ma'] = ta.sma(data.close, length=window)
    return data

def find_signal(open,session_high,session_low,gmt_hour,pre_rsi,pre_ma):
    if open < session_low and gmt_hour >= 8 and gmt_hour < 12 and pre_rsi < 30 and open < pre_ma:
        return 'sell'
    elif open > session_high and gmt_hour >= 8 and gmt_hour < 12 and pre_rsi > 70 and open > pre_ma:
        return 'buy'
    
    # if open<session_low and gmt_hour>=8 and gmt_hour<12:
    #     return 'sell'
    # elif open>session_high and gmt_hour>=8 and gmt_hour<12:
    #     return 'buy'
        
def calculate_sl_tp(open_price, session_high, session_low, atr, signal):
    if signal == 'buy':
        sl = session_low - atr
        tp = open_price + 2 * atr
        # if (tp-open_price)/open_price>0.002:
        #     tp=open_price+open_price*0.002
    elif signal == 'sell':
        sl = session_high + atr
        tp = open_price - 2 * atr
    return sl, tp

        
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
    def __init__(self,open_datetime,open_price,order_type,volume,sl,tp,symbol,is_trade):
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
        self.reason=None

    def close_position(self,close_date_time,close_price,reason):
        self.close_datetime=close_date_time
        self.close_price=close_price
        self.reason=reason
        if 'JPY' in self.symbol:
            self.profit=(self.close_price-self.open_price)*self.volume*0.0094 if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume*0.0094
        else:
            self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status='closed'
   
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
            'reason':self.reason
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
        
    def add_position(self,position):
        self.positions.append(position)

    def trading_allowed(self):
        for pos in self.positions:
            if pos.status=='open':
                return False
        return True
    
    def run(self,trade):
        
        is_trade=0
        trade_signal=None
        
        for i, data in self.data.iterrows():  
            
            # print(i)

            # print(len(self.data))

            if i>=1:
                
                pre_row=self.data.iloc[i-1]
            
                if i<len(self.data)-1:
                
                    next_row=self.data.iloc[i + 1]

                    if not pre_row.empty :
                        # print(pre_row.buy_cnt)
                        # print(data.buy_cnt)
                        # print(data.time)
                        # print(data.buy_cnt)
                        # print(is_trade)
                        if is_trade==0  and data.signal=='buy':
                            # print(f'123-{data.time}')
                            is_trade=1.0
                            trade_signal='buy'
                        
                    
                    if trade==True:
                        
                        if is_trade==1.0 and self.trading_allowed() :
                            order_price=data.open
                            if data.low<=order_price:
                                # print(f'456-{data.time}')
                                sl,tp=calculate_sl_tp(order_price,pre_row.session_high_y, pre_row.session_low_y, pre_row.atr,data.signal)
                                self.add_position(position(data.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade))
                                is_trade=0
                            else: is_trade=0
                                
                        for pos in self.positions:
                            
                            if pos.status=='open' and data.time>=pos.open_datetime:
                                
                                df123=self.get_positions_df()
                                if not df123.empty:
                                    profit= df123['pnl_close'].iloc[-1]
                                    
                                if pos.order_type=='buy' and 17>data.gmt_hour>=8:
                                    if 'JPY' in currency:
                                        total_profit=(data.low-pos.open_price)*pos.volume*0.0094+profit
                                    else:
                                        total_profit=(data.low-pos.open_price)*pos.volume+profit
                                elif pos.order_type=='sell' and 17>data.gmt_hour>=8:
                                    
                                    if 'JPY' in currency:  
                                        total_profit=(pos.open_price-data.high)*pos.volume*0.0094+profit
                                    else:
                                        total_profit=(pos.open_price-data.high)*pos.volume+profit   
                                    
                                if total_profit<profit/2 and  pos.order_type=='buy':
                                    pos.close_position(data.time,data.low,'broke ware house')
                                    is_trade=0
                                    trade=False
                                elif total_profit<profit/2 and  pos.order_type=='sell':
                                    pos.close_position(data.time,data.high,'broke warehouse')
                                    is_trade=0
                                    trade=False
                                elif data.gmt_hour>=17:
                                    pos.close_position(data.time,data.open,'times up')
                                    is_trade=0
                                elif (pos.sl>=data.low and pos.order_type=='buy') :
                                    pos.close_position(data.time,pos.sl,'buy stoploss')
                                    is_trade=0
                                elif (pos.sl<=data.high and pos.order_type=='sell'):
                                    pos.close_position(data.time,pos.sl,'sell stoploss')
                                    is_trade=0
                                elif (pos.tp<=data.high and pos.order_type=='buy'):
                                    pos.close_position(data.time,pos.tp,'buy target profit')
                                    is_trade=0
                                elif (pos.tp>=data.low and pos.order_type=='sell'):
                                    pos.close_position(data.time,pos.tp,'sell target profit')
                                    is_trade=0
        return self.get_positions_df()

def last_sunday_of_month(year, month):
    # Get the last day of the given month
    last_day_of_month = dt.date(year, month, 1) + dt.timedelta(days=32)
    last_day_of_month = last_day_of_month.replace(day=1) - dt.timedelta(days=1)
    
    # Find the last Sunday
    while last_day_of_month.weekday() != 6:  # 6 represents Sunday
        last_day_of_month -= dt.timedelta(days=1)
    
    # Combine date with a specific time (midnight)
    last_sunday_datetime = dt.datetime.combine(last_day_of_month, dt.time.min)
    
    return last_sunday_datetime

def get_session(hour):
    if 0<=hour<8:
        return 'asian session'
    elif 8<=hour<17:
        return 'trading session'
    else: return 'close session'




df1=pd.DataFrame()
df2=pd.DataFrame()
j=0
volumes = list(range(1000, 1000 + 1000, 1000))
years=list(range(2020, 2024 + 1, 1))
symbol=['EURJPY']


# symbols=mt.symbols_get()
# df3=pd.DataFrame(symbols)
# a=df3.iloc[:,[93,95]]
# a.reset_index(inplace=True)
# # a.to_csv('E:/EA/bollinger-bands/all_main_sybol.csv')
# b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
# # c=b[(~b.iloc[:,1].str.contains('.a')) & b.iloc[:,1].str.contains('JPY')]
# c=b[(~b.iloc[:,1].str.contains('.a')) & ~b.iloc[:,1].str.contains('JPY')]
# symbol=c.iloc[:,1]


df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol','is_trade','reason'])

for year in years:
    print(year)
    last_day_march=last_sunday_of_month(year, 3)
    last_day_oct=last_sunday_of_month(year, 10)
    for currency in symbol:
        # currency='NZDCAD'
        print(f'{currency}--start')
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_M30,datetime(year,1,1), datetime(year,12,31))
        
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour


        df['time_gmt'] = np.where( (df['time']>=last_day_march) & (df['time'] <= last_day_oct), 
                                df['time'] - pd.Timedelta(hours=3),
                                df['time'] - pd.Timedelta(hours=2))
        df['gmt_hour']=df['time_gmt'].dt.hour
        df['gmt_date']=df['time_gmt'].dt.date

        df['session']=df['gmt_hour'].apply(get_session)

        df_by_date=df.groupby(['gmt_date','session'],as_index=False).agg(
        session_high=('high','max'),
        session_low=('low','min')
        )

        df=df.merge(df_by_date,on=['gmt_date','session'],how='left')
        df=df.merge(df_by_date[df_by_date['session']=='asian session'],on=['gmt_date'],how='left')
        df=rsi(df,20)
        df['low_rsi']=ta.rsi(df.low, length=20)
        df['high_rsi']=ta.rsi(df.high, length=20)
        df = moving_average(df, 20)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['prev_rsi'] = df['rsi'].shift(1)
        df['prev_ma'] = df['ma'].shift(1)
        df.dropna(subset=['prev_ma'], inplace=True)
        df['signal']=np.vectorize(find_signal)(df['open'],df['session_high_y'],df['session_low_y'],df['gmt_hour'],df['rsi'],df['prev_ma'])
        df['buy_cnt']=count_signal_buy(df,'signal')
        df['sell_cnt']=count_signal_sell(df, 'signal')


        # df['stoploss']=df['session_high']-(df['session_high']-df['session_low'])/2
        df.reset_index(inplace=True)
        df.to_csv(f'C:/c/EA/London_break_out/M15/b_{year}_opi_1.0.csv',index=False)
        print(f'{currency} have been got and start run the strategy')
        for volume in volumes:
            print(volume)
            london_strategy=Strategy(df,300,volume)
            trade=True
            result=london_strategy.run(trade)
            result.dropna(inplace=True)
            last=result[-1:]
            df1=pd.concat([df1,result])
            df2=pd.concat([df2,last])
            j=j+1
            print(f'{currency} have finished-{j}')
        df=df.merge(df1,how='left',left_on=['time'],right_on=['open_datetime'])
        df.to_csv(f'C:/c/EA/London_break_out/M15/b_{year}_opi_result_1.0.csv',index=False)
        
df1['win_rate']=np.where(df1['profit']<0,0,1)
df1['year']=df1['close_datetime'].dt.year
win_result=df1.groupby(['year','win_rate','volume']).agg({'open_datetime':"count"}).reset_index()
pivot_table = win_result.pivot_table(index=['year','win_rate'], columns='volume', values='open_datetime')
# col_sums = win_result['open_datetime'].sum()
# win_result['win']=win_result['open_datetime'].div(col_sums,axis=0)

df2['year']=df2['close_datetime'].dt.year
revenue_result=df2.groupby(['year','volume']).agg({'pnl_close':"sum"})
revenue_result = revenue_result.unstack()

print(pivot_table)

print(revenue_result)
    
df1.to_csv(f'C:/c/EA/London_break_out/M15/result_detail_volumn_rsi_opi_1.0.csv')
df2.to_csv(f'C:/c/EA/London_break_out/M15/final_result_volumn_detail_rsi_opi_1.0.csv')
# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_opiti_5.0.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_opiti_5.0.csv')
# 'E:/EA/bollinger-bands/H1_year'
print('finish')
