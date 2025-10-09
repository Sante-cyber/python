import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
from common import login,password,server
import pytz
import datetime as dt

login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)

def find_signal(open,session_high,session_low,gmt_hour):
        if open<session_low and gmt_hour>=8 and gmt_hour<12:
            return 'sell'
        elif open>session_high and gmt_hour>=8 and gmt_hour<12:
            return 'buy'

class position:
    def __init__(self,open_datetime,open_price,order_type,volume,sl,tp,symbol):
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
        self.reason=None

    def close_position(self,close_date_time,close_price,reason):
        self.close_datetime=close_date_time
        self.close_price=close_price
        self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status='closed'
        self.reason=reason
   
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
            'symbol':self.symbol
        }

class Strategy:

    def __init__(self,df,starting_balance,volume):
        self.starting_balance=starting_balance
        self.volume=volume
        self.positions=[]
        self.data=df
    
    def get_positions_df(self):
        df=pd.DataFrame([position._asdict() for position in self.positions])
        df['pnl_close']=df['profit'].cumsum()+self.starting_balance
        return df
        
    def add_position(self,position):
        self.positions.append(position)

    def trading_allowed(self):
        for pos in self.positions:
            if pos.status=='open':
                return False
        return True
    
    def run(self,trade):
        
            for i, data in self.data.iterrows():  
              if trade==True:
                  
                if data.signal=='buy' and self.trading_allowed():
                    self.add_position(position(data.time_gmt,data.open,data.signal,self.volume,data.stoploss,None,currency))
                elif data.signal=='sell' and self.trading_allowed():
                    self.add_position(position(data.time_gmt,data.open,data.signal,self.volume,data.stoploss,None,currency))

                for pos in self.positions:
                    if pos.status=='open':
                        # profit=(data.close-pos.open)*pos.volume if pos.order_type=='buy' else (pos.open_price-data.close)*pos.volume
                        # equity={
                        #         'open_datetime':pos.open_datetime,
                        #         'open_price':pos.open_price,
                        #         'order_type':pos.order_type,
                        #         'volume': pos.volume,
                        #         'sl':pos.sl,
                        #         'tp':pos.tp,
                        #         'close_datetime':data.time,
                        #         'close_price':data.close,
                        #         'profit':profit,
                        #         'status':pos.status,
                        #         'symbol':pos.symbol
                        #     }
                        # df1=df1.append(equity, ignore_index=True)
                        df123=self.get_positions_df()
                        # print(df123)
                        if not df123.empty:
                            profit= df123['pnl_close'].iloc[-1]
                        #    print(profit)
                        if pos.order_type=='buy':
                            total_profit=(data.low-pos.open_price)*pos.volume+profit
                        else:
                            total_profit=(pos.open_price-data.high)*pos.volume+profit
                        if total_profit<profit/2 and  pos.order_type=='buy':
                            pos.close_position(data.time,data.low)
                            trade=False
                        elif total_profit<profit/2 and  pos.order_type=='sell':
                            pos.close_position(data.time,data.high)
                            trade=False
                        elif data.gmt_hour>=17:
                            pos.close_position(data.time,data.open,'times up')
                        elif (pos.sl>=data.low and pos.order_type=='buy') :
                            pos.close_position(data.time,pos.sl,'buy stoploss')
                        elif (pos.sl<=data.high and pos.order_type=='sell'):
                            pos.close_position(data.time,pos.sl,'sell stoploss')
                        elif (pos.tp<=data.high and pos.order_type=='buy'):
                            pos.close_position(data.time,pos.tp,'buy target profit')
                        elif (pos.tp>=data.low and pos.order_type=='sell'):
                            pos.close_position(data.time,pos.tp,'sell target profit')
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
    elif 8<=hour<=17:
        return 'trading session'
    else: return 'close session'


year = 2023
month=3
last_day_march=last_sunday_of_month(year, month)
month=10
last_day_oct=last_sunday_of_month(year, month)

currency='GBPJPY'
bars=mt.copy_rates_range(currency,mt.TIMEFRAME_M15,datetime(year,1,1),datetime(year,12,31))
# datetime.now()
df=pd.DataFrame(bars)
df['time']=pd.to_datetime(df['time'],unit='s')

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
df['stoploss']=df['session_high_y']-(df['session_high_y']-df['session_low_y'])/2

trades=pd.DataFrame(columns=['state','order_type','open_time','open_price','close_time','close_price','close_reason'])

for i,x in df.iterrows():
    #open trade logic
    open_cond1=12>x['gmt_hour']>=8
    num_open_trades=trades[trades['state']=='open'].shape[0]
    open_cond2=num_open_trades==0
    # print(trades)
    if open_cond1 and open_cond2 and x['open']>x['session_high']:
        trades.loc[len(trades),trades.columns]=['open','buy',x['time_gmt'],x['open'],None,None,None]
    elif open_cond1 and open_cond2 and x['open']<x['session_low']:
        trades.loc[len(trades),trades.columns]=['open','sell',x['time_gmt'],x['open'],None,None,None]
    # print(x,open_cond1,open_cond2,trades,num_open_trades)
    if num_open_trades==0:
        continue
        
    #close trade logic
    close_cond1=x['gmt_hour']>=17
    open_trade_order_type=trades[trades['state']=='open'].iloc[0]['order_type']
    close_cond2=x['low']<=x['stoploss'] if open_trade_order_type=='buy'\
                                        else x['high']>=x['stoploss']
    # print(close_cond1,close_cond2)
    if close_cond1:
        trades.loc[trades['state']=='open',['state','close_time','close_price','close_reason']]=['closed',x['time'],x['open'],'time up']
    if close_cond2:
        trades.loc[trades['state']=='open',['state','close_time','close_price','close_reason']]=['closed',x['time'],x['stoploss'],'touch stop loss']
    
trades
df.to_csv('C:/c/EA/London_break_out/b.csv')

# fig=go.Figure(
#     data=[go.Candlestick(
#         name='GBPJPY OHLC',
#         x=df['time_gmt'],
#         open=df['open'],
#         high=df['high'],
#         low=df['low'],
#         close=df['close'],
#     )]
# )
# fig.update_layout(xaxis_rangeslider_visible=False,height=600)
# fig.add_trace(go.Scatter(name='asia_high',x=df['time_gmt'],y=df['session_high']))
# fig.add_trace(go.Scatter(name='asia_low',x=df['time_gmt'],y=df['session_low']))
# fig.add_trace(go.Scatter(name='stoploss',x=df['time_gmt'],y=df['stoploss']))
# fig.show()

# df.to_csv('E:/EA/a.csv')


df1=pd.DataFrame()
df2=pd.DataFrame()
j=0
volumes = list(range(1000, 10000 + 1000, 1000))
years=list(range(2020, 2024 + 1, 1))
symbol=['GBPNZD','GBPCAD','NZDCAD','GBPAUD','GBPUSD']

# symbol=['GBPAUD']
# # years=[2024]
# # volumes=[10000]

# # aa=a.iloc[40:]



# symbols=mt.symbols_get()
# df3=pd.DataFrame(symbols)
# a=df3.iloc[:,[93,95]]
# a.reset_index(inplace=True)
# # a.to_csv('E:/EA/bollinger-bands/all_main_sybol.csv')
# b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
# c=b[(~a.iloc[:,1].str.contains('.a'))]

# symbol=c.iloc[:,1]


df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol','reason'])


for year in years:
    print(year)
    month=3
    last_day_march=last_sunday_of_month(year, month)
    month=10
    last_day_oct=last_sunday_of_month(year, month)
    for currency in symbol:
        # currency='NZDCAD'
        print(f'{currency}--start')
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_M15,datetime(year,1,1), datetime(year,12,31))
        # bars=mt.copy_rates_from_pos(currency,mt.TIMEFRAME_H1,1,20)
      
#  datetime.now()
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour

        # fig=px.line(df,x='time',y='close')
        # fig.show()

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

        df=df.merge(df_by_date,on=['gmt_date'],how='left')
        df['stoploss']=df['session_high']-(df['session_high']-df['session_low'])/2

        df['signal']=np.vectorize(find_signal)(df['open'],df['session_high'],df['session_low'],df['gmt_hour'])
        df.reset_index(inplace=True)
        df.to_csv('E:/EA/London_Breakout/M15/a.csv')
        # df.to_csv('C:/c/EA/bollinger-bands/H4_year/a.csv')
        # df.to_csv('C:/Ally/a.csv')
        print(f'{currency} have been got and start run the strategy')
        for volume in volumes:
            print(volume)
            bollinger_strategy=Strategy(df,300,volume)
            trade=True
            result=bollinger_strategy.run(trade)
            # print(result)
            result.dropna(inplace=True)
            last=result[-1:]
            df1=pd.concat([df1,result])
            df2=pd.concat([df2,last])
            j=j+1
            print(f'{currency} have finished-{j}')

df1['win_rate']=np.where(df1['profit']<0,0,1)
win_result=df1.groupby('win_rate').agg({'open_datetime':"count"}).reset_index()
col_sums = win_result['open_datetime'].sum()
win_result['win']=win_result['open_datetime'].div(col_sums,axis=0)

df2['year']=df2['close_datetime'].dt.year
revenue_result=df2.groupby(['year','volume']).agg({'pnl_close':"sum"})
revenue_result = revenue_result.unstack()

print(win_result)

print(revenue_result)
    
df1.to_csv(f'C:/c/EA/bollinger-bands/H4_year/result_detail_volumn_rsi.csv')
df2.to_csv(f'C:/c/EA/bollinger-bands/H4_year/final_result_volumn_detail_rsi.csv')
# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_rsi.csv')
# 'E:/EA/bollinger-bands/H1_year'
print('finish')

# Example usage:

