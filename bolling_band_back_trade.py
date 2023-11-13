import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
from python.common import login,password,server
import numpy as np

symbol='GBPUSD'
TIMEFRAME=mt.TIMEFRAME_D1
VOLUME=1.0
DEVIATION=20
MAGIC=10
SMA_PERIOD=20
STANDARD_DEVIATIONS=2
TP_SD=2
SL_SD=1


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


mt.initialize()
mt.login(login,password,server)

symbols=mt.symbols_get()
df=pd.DataFrame(symbols)
a=df.iloc[:,[93,95]]
a.reset_index(inplace=True)
b=a[(a.iloc[:,2].str.contains('Majors')) |(a.iloc[:,2].str.contains('Minors')) | (a.iloc[:,2].str.contains('Exotics'))]
c=b[~a.iloc[:,1].str.contains('.a')]
df1=pd.DataFrame()
df2=pd.DataFrame()
for currency in c.iloc[:,1]:
    bars=mt.copy_rates_range(currency,mt.TIMEFRAME_D1,datetime(2020,1,1),datetime.now())
    bars

    df=pd.DataFrame(bars)
    df['time']=pd.to_datetime(df['time'],unit='s')

    # fig=px.line(df,x='time',y='close')
    # fig.show()

    df['sma']=df['close'].rolling(30).mean()
    df['sd']=df['close'].rolling(30).std()
    df['lb']=df['sma']-2*df['sd']
    df['ub']=df['sma']+2*df['sd']
    df.dropna(inplace=True)

    # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
    # fig.show()

    def find_signal(close,lower_band,upper_band):
        if close<lower_band:
            return 'buy'
        elif close>upper_band:
            return 'sell'
        
    df['signal']=np.vectorize(find_signal)(df['close'],df['lb'],df['ub'])

    # print(df)

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
            df['pnl']=df['profit'].cumsum()+self.starting_balance
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
                if data.signal=='buy' and self.trading_allowed():
                    sl=data.close-3*data.sd
                    tp=data.close+2*data.sd
                    self.add_position(position(data.time,data.close,data.signal,self.volume,sl,tp,currency))
                elif data.signal=='sell' and self.trading_allowed():
                    sl=data.close+3*data.sd
                    tp=data.close-2*data.sd
                    self.add_position(position(data.time,data.close,data.signal,self.volume,sl,tp,currency))

                for pos in self.positions:
                    if pos.status=='open':
                        if (pos.sl>=data.close and pos.order_type=='buy'):
                            pos.close_position(data.time,pos.sl)
                        elif (pos.sl<=data.close and pos.order_type=='sell'):
                            pos.close_position(data.time,pos.sl)
                        elif (pos.tp<=data.close and pos.order_type=='buy'):
                            pos.close_position(data.time,pos.tp)
                        elif (pos.tp>=data.close and pos.order_type=='sell'):
                            pos.close_position(data.time,pos.tp)
            return self.get_positions_df()
        
    bollinger_strategy=Strategy(df,200,1000)
    result=bollinger_strategy.run()
    result.dropna(inplace=True)
    last=result[-1:]
    df1=pd.concat([df1,result])
    df2=pd.concat([df2,last])
    df1.to_csv('E:/EA/bollinger-bands/result_detail.csv')
    df2.to_csv('E:/EA/bollinger-bands/final_result_detail.csv')
    # fig=px.line(df,x='time',y=['close','sma','lb','ub'])
    # for i,position in result.iterrows():
    #     if position.status=='closed':
    #         fig.add_shape(type='line',x0=position.open_datetime,y0=position.open_price,x1=position.close_datetime,y1=position.close_price)
    #         line=dict(
    #             color='green' if position.profit>=0 else "dark",
    #             width=3
    #         )
    # fig.show()



