import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
from common import login,password,server

login=51339268
password='UZcMdrwV'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)


def find_signal(close,lower_band,upper_band):
        if close<lower_band:
            return 'buy'
        elif close>upper_band:
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
        self.profit=None
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

    def __init__(self,df,starting_balance,volume,df1):
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
    
    def run(self):
        for i, data in self.data.iterrows():
            if data.signal=='buy' and data.hour>=9 and data.hour<=18 and self.trading_allowed():
                sl=data.close-1*data.sd
                tp=data.close+1.5*data.sd
                self.add_position(position(data.time,data.close,data.signal,self.volume,sl,tp,currency))
            elif data.signal=='sell' and self.trading_allowed():
                sl=data.close+1*data.sd
                tp=data.close-1.5*data.sd
                self.add_position(position(data.time,data.close,data.signal,self.volume,sl,tp,currency))

            for pos in self.positions:
                if pos.status=='open':
                    profit=(data.close_price-pos.open_price)*pos.volume if pos.order_type=='buy' else (pos.open_price-data.close_price)*pos.volume
                    equity={
                            'open_datetime':pos.open_datetime,
                            'open_price':pos.open_price,
                            'order_type':pos.order_type,
                            'volume': pos.volume,
                            'sl':pos.sl,
                            'tp':pos.tp,
                            'close_datetime':data.close_datetime,
                            'close_price':data.close_price,
                            'profit':profit,
                            'status':pos.status,
                            'symbol':pos.symbol
                        }
                    df1=df1.append(equity, ignore_index=True)
                    if (pos.sl>=data.close and pos.order_type=='buy'):
                        pos.close_position(data.time,pos.sl)
                    elif (pos.sl<=data.close and pos.order_type=='sell'):
                        pos.close_position(data.time,pos.sl)
                    elif (pos.tp<=data.close and pos.order_type=='buy'):
                        pos.close_position(data.time,pos.tp)
                    elif (pos.tp>=data.close and pos.order_type=='sell'):
                        pos.close_position(data.time,pos.tp)
        return self.get_positions_df()


symbols=mt.symbols_get()
df=pd.DataFrame(symbols)
a=df.iloc[:,[93,95]]
a.reset_index(inplace=True)
# a.to_csv('E:/EA/bollinger-bands/all_main_sybol.csv')
b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors'))]
c=b[(~a.iloc[:,1].str.contains('.a'))]
# c=b[(~a.iloc[:,1].str.contains('.a')) & (~a.iloc[:,1].str.contains('EURZAR')) & (~a.iloc[:,1].str.contains('EURTRY')) 
#     & (~a.iloc[:,1].str.contains('NOK')) & (~a.iloc[:,1].str.contains('SEKJPY')) & (~a.iloc[:,1].str.contains('SGDJPY'))]

df1=pd.DataFrame()
df2=pd.DataFrame()
j=0

a=c.iloc[:,1]
aa=a.iloc[40:]

for currency in c.iloc[:,1]:
    print(f'{currency}--start')
    bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(2023,1,1),datetime.now())
    bars
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
 
       
    df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'])
    print(f'{currency} have been got and start run the strategy')
    df1 = pd.DataFrame(columns=['open_datetime', 'open_price', 'order_type', 'volume', 'sl', 'tp', 'close_datetime', 'close_price', 'profit', 'status', 'symbol'])
    bollinger_strategy=Strategy(df,200,1000,df1)
    result=bollinger_strategy.run()
    result.dropna(inplace=True)
    last=result[-1:]
    df1=pd.concat([df1,result])
    df2=pd.concat([df2,last])
    j=j+1
    print(f'{currency} have finished-{j}')
df1.to_csv('E:/EA/bollinger-bands/result_detail.csv')
df2.to_csv('E:/EA/bollinger-bands/final_result_detail.csv')
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



