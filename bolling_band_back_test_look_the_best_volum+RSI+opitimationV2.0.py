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


def rsi(data,window):
    data['rsi']=ta.rsi(df.close, length=window)
    data['overbought']=68
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
            'symbol':self.symbol,
            'is_trade':self.is_trade
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
            is_trade=0
            trade_signal=None
            pre_row=pd.DataFrame()
            for i, data in df.iterrows():
                
              if i>1:
                pre_row=df.iloc[i-1]
                pre_2_row=df.iloc[i-2]
                
              if i<len(df)-1:
                next_row=df.iloc[i + 1]
                if not pre_row.empty :
                    if is_trade==0 and data.signal=='buy' and data.buy_cnt==1:
                        is_trade=1
                        trade_signal='buy'
                    elif is_trade==0 and data.signal=='sell' and data.buy_cnt==1:
                        is_trade=2
                        trade_signal='sell'
                if trade==True:
                    if is_trade==1  and self.trading_allowed():
                        if data.buy_cnt==0 and pre_row.buy_cnt==1:
                            # print(f'{data}--{next_row}')
                            sl=next_row.close-1*next_row.sd
                            tp=next_row.close+1.8*next_row.sd
                            self.add_position(position(next_2_row.time,next_row.close,trade_signal,self.volume,sl,tp,currency,is_trade))
                        else: is_trade=0
                    elif is_trade==2 and  self.trading_allowed():
                        if next_row.low_point==1 and next_2_row.high_point!=1:
                          if next_4_row.low<=next_3_row.close:
                            sl=next_3_row.close-0.6*next_3_row.sd
                            tp=next_3_row.close+0.9*next_3_row.sd
                            self.add_position(position(next_4_row.time,next_3_row.close,trade_signal,self.volume,sl,tp,currency,is_trade))
                          else: is_trade=0
                        elif next_row.low_point==1 and next_2_row.high_point==1 and next_3_row.low_point!=1:
                          if next_5_row.low<=next_4_row.close:
                            sl=next_4_row.close-0.6*next_4_row.sd
                            tp=next_4_row.close+0.9*next_4_row.sd
                            self.add_position(position(next_5_row.time,next_4_row.close,trade_signal,self.volume,sl,tp,currency,is_trade))
                          else: is_trade=0                      
                        # elif next_row.low_point==1 and next_2_row.high_point==1 and next_3_row.low_point!=1:                        
                    elif is_trade==3 and self.trading_allowed():
                        if next_2_row.high>=next_row.close:
                            # print(f'{data}--{next_row}')
                            sl=next_row.close+1*next_row.sd
                            tp=next_row.close-1.8*next_row.sd
                            self.add_position(position(next_2_row.time,next_row.close,trade_signal,self.volume,sl,tp,currency,is_trade))
                        else: is_trade=0
                    elif is_trade==4 and self.trading_allowed():
                        # if data.over_70==5:
                        if next_row.high_point==1 and next_2_row.low_point!=1:
                          if next_4_row.high>=next_3_row.close:
                            sl=next_3_row.close+0.6*next_3_row.sd
                            tp=next_3_row.close-0.9*next_3_row.sd
                            self.add_position(position(next_4_row.time,next_3_row.close,trade_signal,self.volume,sl,tp,currency,is_trade))
                          else: is_trade=0
                        elif next_row.high_point==1 and next_2_row.low_point==1 and next_3_row.high_point!=1:
                          order_price=(next_4_row.high+next_4_row.close)/2
                          if next_5_row.high>=order_price:
                            sl=order_price+0.6*next_4_row.sd
                            tp=order_price-0.9*next_4_row.sd
                            self.add_position(position(next_5_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade))
                          else: is_trade=0
                    for pos in self.positions:
                        # print(pos.status)
                        if pos.status=='open' and data.time>=pos.open_datetime:
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
                            if pos.order_type=='buy' :
                                total_profit=(data.low-pos.open_price)*pos.volume+profit
                            else:
                                total_profit=(pos.open_price-data.high)*pos.volume+profit
                            if total_profit<profit/2 and  pos.order_type=='buy':
                                pos.close_position(data.time,data.low)
                                is_trade=0
                                trade=False
                            elif total_profit<profit/2 and  pos.order_type=='sell':
                                pos.close_position(data.time,data.high)
                                is_trade=0
                                trade=False
                            elif (pos.sl>=data.low and pos.order_type=='buy'):
                                pos.close_position(data.time,pos.sl)
                                is_trade=0
                            elif (pos.sl<=data.high and pos.order_type=='sell'):
                                pos.close_position(data.time,pos.sl)
                                is_trade=0
                            elif (pos.tp<=data.high and pos.order_type=='buy'):
                                pos.close_position(data.time,pos.tp)
                                is_trade=0
                            elif (pos.tp>=data.low and pos.order_type=='sell'):
                                pos.close_position(data.time,pos.tp)
                                is_trade=0
            return self.get_positions_df()


df1=pd.DataFrame()
df2=pd.DataFrame()
j=0
volumes = list(range(1000, 1000 + 1000, 1000))
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


df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol','is_trade'])

for year in years:
    print(year)
    for currency in symbol:
        # currency='NZDCAD'
        print(f'{currency}--start')
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year,1,1), datetime(year,12,31))
        # bars_h1=mt.copy_rates_range(currency,mt.TIMEFRAME_H1,datetime(year,1,1), datetime(year,12,31))
        # bars=mt.copy_rates_from_pos(currency,mt.TIMEFRAME_H1,1,20)
      
#  datetime.now()
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour
        
        # df_h1=pd.DataFrame(bars_h1)
        # df_h1['time']=pd.to_datetime(df_h1['time'],unit='s')
        # df_h1['hour']=df_h1['time'].dt.hour
        # fig=px.line(df,x='time',y='close')
        # fig.show()

        df['sma']=df['close'].rolling(20).mean()
        df['sd']=df['close'].rolling(20).std()
        df['lb']=df['sma']-2*df['sd']
        df['ub']=df['sma']+2*df['sd']
        
        df=find_lower_high_point(df,'tick_volume')
        df.dropna(subset=['sd'], inplace=True)
        df=rsi(df,14)
        df['over_70'] = count_consecutive_above(df, 'rsi',70)
        df['lower_30'] = count_consecutive_lower(df, 'rsi',30)
        # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
        # fig.show()
    
        # df=rsi(df,14)
        df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'],df['rsi'],df['overbought'],df['oversold'])
        df['buy_cnt']=count_signal_buy(df,'signal')
        df['sell_cnt']=count_signal_sell(df, 'signal')
        df.reset_index(inplace=True)
        # df.to_csv(f'E:/EA/bollinger-bands/H4_year/a_{year}_opi.csv')
        df.to_csv(f'C:/c/EA/bollinger-bands/H4_year/b_{year}_opi.csv')
        # df_h1.to_csv(f'C:/c/EA/bollinger-bands/H4_year/b_h1_{year}.csv')
        # df.to_csv('C:/Ally/a.csv')
        print(f'{currency} have been got and start run the strategy')
        for volume in volumes:
            print(volume)
            bollinger_strategy=Strategy(df,200,volume)
            trade=True
            result=bollinger_strategy.run(trade)
            # print(result)
            result.dropna(inplace=True)
            last=result[-1:]
            df1=pd.concat([df1,result])
            df2=pd.concat([df2,last])
            j=j+1
            print(f'{currency} have finished-{j}')
        df=df.merge(df1,how='left',left_on=['time'],right_on=['open_datetime'])
        df.to_csv(f'C:/c/EA/bollinger-bands/H4_year/b_{year}_opi_result.csv',index=False)

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
    
df1.to_csv(f'C:/c/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_opi.csv')
df2.to_csv(f'C:/c/EA/bollinger-bands/H4_year/final_result_volumn_detail_rsi_opi.csv')
# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_opiti.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_opiti.csv')
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



