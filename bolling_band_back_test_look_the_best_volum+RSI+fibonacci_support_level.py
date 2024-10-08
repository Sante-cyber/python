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


def fibonacci_retracement(df):
    retracement_levels = [0, 0.236, 0.382, 0.5, 0.618, 1]  # Fibonacci levels
    for level in retracement_levels:
        col=f'fibonacci_prices_{level}'
        print(col)
        df[col] = df['high_price'] - (df['high_price'] - df['low_price']) * level
    df['fibonacci_support_level']=df['fibonacci_prices_0.236']
    df['fibonacci_resistance_level']=df['fibonacci_prices_0.236']
    return df

def rsi(data,window):
    data['rsi']=ta.rsi(df.close, length=window)
    data['overbought']=68
    data['oversold']=29
    return data

def ema(data,window,backcandles):
    data['ema']=ta.ema(data.close,length=window)
    emasignal=[0]*len(data)
    for row in range(backcandles,len(data)):
        upt=1
        dnt=1
        for i in range(row-backcandles,row+1):
            if max(data.open[i],data.close[i])>=data.ema[i]:
                dnt=0
            if min(data.open[i],data.close[i])<=data.ema[i]:
                upt=0
            if upt==1 and dnt==1:
                emasignal[row]=3
            elif upt==1:
                emasignal[row]=2
            elif dnt==1:
                emasignal[row]=1
    data['emasignal']=emasignal
    return data

def find_lower_high_point(df,type,type1):
    for i in range(1, len(df) - 1):
        if df[type][i] > df[type][i - 1] and df[type][i] > df[type][i + 1]:
            df.at[i, 'high_point'] = 1
        elif df[type1][i] < df[type1][i - 1] and df[type1][i] < df[type1][i + 1]:
            df.at[i, 'low_point'] = 1
    
    return(df)

def find_closest_high_point_price(type,price,index):
    closest_high_point = df[(df[type] > price) & (df['high_point'] == 1) & (df.index < index)]
    if not closest_high_point.empty:
        closest_high_point = closest_high_point.iloc[-1][type]
        return closest_high_point
    else:
        return None

# Function to find the closest low point price before the given price
def find_closest_low_point_price(type,price,index):
    closest_low_point = df[(df[type] < price) & (df['low_point'] == 1) & (df.index < index)]
    if not closest_low_point.empty:
        closest_low_point = closest_low_point.iloc[-1][type]
        return closest_low_point
    else:
        return None

def generate_signal(df,l,backcandles,gap,zone_threshold,price_diff_threshold):
    print(l,backcandles,gap,zone_threshold,price_diff_threshold)
    max_price=df.high[l-backcandles:l-gap].max()
    min_price=df.low[l-backcandles:l-gap].min()
    index_max=df.high[l-backcandles:l-gap].idxmax()
    index_min=df.high[l-backcandles:l-gap].idxmin()
    price_diff=max_price-min_price
    print(price_diff)
    if(df.emasignal[l]==2
       and index_min<index_max
       and price_diff>price_diff_threshold):
        l1=max_price-0.62*price_diff
        l2=max_price-0.78*price_diff
        l3=max_price-0.*price_diff
        if abs(df.close[l]-l1)<zone_threshold and df.high[l-gap:l].min()>l1:
            return('buy',l2,l3,index_min,index_max)
        else:
            return(None,0,0,0,0)
    elif (df.emasignal[l]==1
        and index_min>index_max
        and price_diff>price_diff_threshold):
        l1=min_price+0.62*price_diff
        l2=min_price+0.78*price_diff
        l3=min_price+0.*price_diff
        if abs(df.close[l]-l1) < zone_threshold and df.low[l-gap:l].max()<l1:
            return('sell',l2,l3,index_min,index_max)
        else:
            return(None,0,0,0,0)
    else:
        return(None,0,0,0,0)
        
def find_signal(close,lower_band,upper_band,rsi,overbought,oversold,fibonacci_support_level,fibonacci_resistance_level):
        if close<lower_band and rsi<oversold :
        # and close < fibonacci_support_level:
            return 'buy'
        elif close>upper_band and rsi>overbought and close >fibonacci_resistance_level:
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
                            # sl=0.995*data.close
                            # tp=1.015*data.close
                            self.add_position(position(next_row.time,data.close,data.signal,self.volume,sl,tp,currency))
                    elif data.signal=='sell' and self.trading_allowed():
                        if next_row.high>=data.close:
                            # print(f'{data}--{next_row}')
                            sl=data.close+1*data.sd
                            tp=data.close-2*data.sd
                            # sl=1.005*data.close
                            # tp=0.985*data.close
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
volumes = list(range(1000, 1000 + 1000, 1000))
years=list(range(2020, 2024 + 1, 1))
# symbol=['GBPNZD','GBPCAD','NZDCAD','GBPAUD','GBPUSD']
symbol=['EURAUD']
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
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year-1,1,1), datetime(year,12,31))
        # if year>2020:
        #     bars1=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year-1,4,1), datetime(year-1,12,31))
        #     bars=mt.copy_rates_from_pos(currency,mt.TIMEFRAME_H1,1,20)
        #     df5=pd.DataFrame(bars1)
        #     high_price = df5['close'].max()
        #     low_price = df5['close'].min()
#  datetime.now()
        df=pd.DataFrame(bars)
        df['time']=pd.to_datetime(df['time'],unit='s')
        df['hour']=df['time'].dt.hour
        df['year']=df['time'].dt.year
        
        df=find_lower_high_point(df,'close','close')

        df['previous_high_point_price'] = df.apply(lambda row: find_closest_high_point_price('close',row['close'], row.name), axis=1)
        df['previous_low_point_price'] = df.apply(lambda row: find_closest_low_point_price('close',row['close'], row.name), axis=1)
        
        # df.to_csv('C:/c/EA/bollinger-bands/H4_year/a_rsi.csv')

        df['buy_l1']=df['previous_high_point_price']-0.618*(df['previous_high_point_price']-df['previous_low_point_price'])
        df['sell_l1']=df['previous_high_point_price']-0.382*(df['previous_high_point_price']-df['previous_low_point_price'])
        df['sma']=df['close'].rolling(20).mean()
        df['sd']=df['close'].rolling(20).std()
        df['lb']=df['sma']-2*df['sd']
        df['ub']=df['sma']+2*df['sd']
        
        df=df[df['year']==year]
        
        # df.to_csv('C:/c/EA/bollinger-bands/H4_year/a_rsi.csv')

        df.dropna(subset=['sd'], inplace=True)
        

    
        df=rsi(df,14)
        # df =fibonacci_retracement(df)
        # # fibonacci_support_level = fibonacci_prices[1] 
        # # fibonacci_resistance_level = fibonacci_prices[4]
        
        df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'],df['rsi'],df['overbought'],df['oversold'],df['buy_l1'],df['sell_l1'])
        df.reset_index(inplace=True)
        # df.to_csv('E:/EA/bollinger-bands/H4_year/a_rsi_f.csv')
        df.to_csv('C:/c/EA/bollinger-bands/H4_year/a_rsi.csv')
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
    
df1.to_csv(f'C:/c/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_fibonacci.csv')
df2.to_csv(f'C:/c/EA/bollinger-bands/H4_year/final_result_volumn_detail_rsi_fibonacci.csv')
# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_fibonacci.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_rsi_fibonacci.csv')
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

# df=ema(df,40,5)
# gap_candles=5
# backcandles=10
# signal=[None for i in range(len(df))]    
# tp=[0 for i in range(len(df))]
# sl=[0 for i in range(len(df))]
# minswing=[0 for i in range(len(df))]
# maxswing=[0 for i in range(len(df))]
# for row in range(backcandles, len(df)):
#     gen_sig = generate_signal(df, row, backcandles=backcandles, gap=gap_candles, zone_threshold=0.001, price_diff_threshold=0.001)
#     signal[row] = gen_sig[0]
#     sl[row] = gen_sig[1]
#     tp[row] = gen_sig[2]
#     minswing[row] = gen_sig[3]
#     maxswing[row] = gen_sig[4]

# df['signal'] = signal
# df['sl'] = sl
# df['tp'] = tp
# df['minswing'] = minswing
# df['maxswing'] = maxswing               
        
# df.to_csv('C:/Ally/a.csv')
# fig=px.line(df,x='time',y='close')
# fig.show()

# high_price = df['close'].max()
# low_price = df['close'].min()
# df['high_price1'] = df.apply(lambda row: df.loc[:row.name, 'close'].max(), axis=1)
# df['low_price1'] = df.apply(lambda row: df.loc[:row.name, 'close'].min(), axis=1)
# df['high_price'] = df.apply(lambda row: max(row['high_price1'], high_price), axis=1)
# df['low_price'] = df.apply(lambda row: min(row['low_price1'], low_price), axis=1)

# # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
# # fig.show()