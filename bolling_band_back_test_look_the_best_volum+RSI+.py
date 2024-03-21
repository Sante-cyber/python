import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
import pandas_ta as ta
from common import login,password,server

login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)


def calculate_macd(data, short_window, long_window, signal_window):
    data['ShortEMA'] = data['close'].ewm(span=short_window, min_periods=1, adjust=False).mean()
    data['LongEMA'] = data['close'].ewm(span=long_window, min_periods=1, adjust=False).mean()
    data['MACD'] = data['ShortEMA'] - data['LongEMA']
    data['Sig'] = data['MACD'].ewm(span=signal_window, min_periods=1, adjust=False).mean()
    return data


def rsi(data,window):
    data['rsi']=ta.rsi(df.close, length=window)
    data['overbought']=68
    data['oversold']=28
    return data

def find_signal(close,lower_band,upper_band,rsi,overbought,oversold,macd,sig):
        if close<lower_band and rsi<oversold and macd > Leading_Span_B:
            return 'buy'
        elif close>upper_band and rsi>overbought and Leading_Span_A <Leading_Span_B:
            return 'sell'

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

    def close_position(self,close_date_time,close_price):
        self.close_datetime=close_date_time
        self.close_price=close_price
        self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status='closed'

    def monitor_equity(self,close_date_time,close_price):
        self.close_datetime=close_date_time
        self.close_price=close_price
        self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status='open'
    
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
    
    def get_equity_df(self):
        df=pd.DataFrame([position._asdict() for position in self.positions])
        df['pnl_equity']=df['profit'].cumsum()+self.starting_balance
        return df
    
    def add_position(self,position):
        self.positions.append(position)

    def trading_allowed(self):
        for pos in self.positions:
            if pos.status=='open':
                return False
        return True
    
    def run(self,trade):
        # self.data.
            for i, data in df.iterrows():
                
              if i<len(df)-1:
                next_row=df.iloc[i + 1]
                  
                if trade==True:
                    
                    if data.signal=='buy'  and self.trading_allowed():
                        if next_row.low<=data.close:
                            # print(f'{data}--{next_row}')
                            sl=data.close-1*data.sd
                            tp=data.close+2*data.sd
                            self.add_position(position(next_row.time,data.close,data.signal,self.volume,sl,tp,currency))
                    elif data.signal=='sell' and self.trading_allowed():
                        if next_row.high>=data.close:
                            # print(f'{data}--{next_row}')
                            sl=data.close+1*data.sd
                            tp=data.close-2*data.sd
                            self.add_position(position(next_row.time,data.close,data.signal,self.volume,sl,tp,currency))
            
                    for pos in self.positions:
                        # print(pos.status)
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
                                total_profit=(next_row.low-pos.open_price)*pos.volume+profit
                            else:
                                total_profit=(pos.open_price-next_row.high)*pos.volume+profit
                            if total_profit<profit/2 and  pos.order_type=='buy':
                                pos.close_position(next_row.time,next_row.low)
                                trade=False
                            elif total_profit<profit/2 and  pos.order_type=='sell':
                                pos.close_position(next_row.time,next_row.high)
                                trade=False
                            elif (pos.sl>=next_row.low and pos.order_type=='buy'):
                                pos.close_position(next_row.time,pos.sl)
                            elif (pos.sl<=next_row.high and pos.order_type=='sell'):
                                pos.close_position(next_row.time,pos.sl)
                            elif (pos.tp<=next_row.high and pos.order_type=='buy'):
                                pos.close_position(next_row.time,pos.tp)
                            elif (pos.tp>=next_row.low and pos.order_type=='sell'):
                                pos.close_position(next_row.time,pos.tp)
            return self.get_positions_df()


df1=pd.DataFrame()
df2=pd.DataFrame()
j=0
volumes = list(range(1000, 10000 + 1000, 1000))
years=list(range(2020, 2024 + 1, 1))
# symbol=['GBPNZD','GBPCAD','NZDCAD','GBPAUD','GBPUSD']

symbol=['GBPAUD']
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


df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol'])

for year in years:
    print(year)
    for currency in symbol:
        # currency='NZDCAD'
        print(f'{currency}--start')
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year,1,1), datetime(year,12,31))
        # bars=mt.copy_rates_from_pos(currency,mt.TIMEFRAME_H1,1,20)
      
#  datetime.now()
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour

        # fig=px.line(df,x='time',y='close')
        # fig.show()

        df['sma']=df['close'].rolling(20).mean()
        df['sd']=df['close'].rolling(20).std()
        df['lb']=df['sma']-2*df['sd']
        df['ub']=df['sma']+2*df['sd']
        df.dropna(inplace=True)
    

        # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
        # fig.show()
    
        df=rsi(df,14)
        df=calculate_ichimoku_cloud(df,9,26,52)
        df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'],df['rsi'],df['overbought'],df['oversold'],df['Leading_Span_A'], df['Leading_Span_B'])
        df.reset_index(inplace=True)
        # df.to_csv('E:/EA/bollinger-bands/H4_year/a.csv')
        df.to_csv('C:/c/EA/bollinger-bands/H4_year/a.csv')
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
df1['year']=df1['close_datetime'].dt.year
win_result=df1.groupby(['year','win_rate']).agg({'open_datetime':"count"}).reset_index()
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
    # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
    # for i,position in result.iterrows():
    #     if position.status=='closed':
    #         fig.add_shape(type='line',x0=position.open_datetime,y0=position.open_price,x1=position.close_datetime,y1=position.close_price)
    #         line=dict(
    #             color='green' if position.profit>=0 else "dark",
    #             width=3
    #         )
    # fig.show()



