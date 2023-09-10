import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
from datetime import datetime
from python.common import login,password,server


mt.login(login,password,server)

symbol='AUDUSD'
timeframe=mt.TIMEFRAME_M10
start_date=datetime(2023,1,1)
end_date=datetime(2023,7,1)
trade_volume=0.1
commission=0.00007

bars=pd.DataFrame(mt.copy_rates_range(symbol,timeframe,start_date,end_date))
bars['time']=pd.to_datetime(bars['time'],unit='s')
bars['trade_volume']=trade_volume
bars

bars['sma_100']=bars['close'].rolling(100).mean()
bars['sma_10']=bars['close'].rolling(10).mean()
bars['hour']=bars['time'].dt.hour
bars

bars2=bars.dropna().copy()

def get_signal(x):
    if 9<=x['hour']<=18:
        if x['sma_10']>x['sma_100']:
            return 1
        elif x['sma_10']<x['sma_100']:
            return -1
    return 0

bars2['signal']=bars2.apply(get_signal,axis=1)
bars2['prev_price']=bars2['close'].shift(1)
bars2['price_change']=bars2['close']-bars2['prev_price']

bars2['signal_change']=(bars2['signal']-bars2['signal'].shift(1)).abs()
bars2['commission']=bars2.apply(lambda x:commission*x['signal_change']*x['trade_volume'],axis=1)*100000
bars2

bars3=bars2.dropna().copy()
bars3['profit']=bars3['signal']*bars3['price_change']*bars3['trade_volume']*100000
bars3['grossip_profit']=bars3['profit'].cumsum()
bars3['net_profit']=bars3['grossip_profit']-bars3['commission'].cumsum()
print(bars3)

fig=px.line(bars3,'time', ['grossip_profit','net_profit'],title='AUDUSD Backtest MA Trendfollowing')
fig.show()
