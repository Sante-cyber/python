import MetaTrader5 as mt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from common import login,password,server
import pandas_ta as ta


login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)


def get_day_low(data,windows):
    data[f'low_{windows}']=data['low'].rolling(window=windows).min()
    data['low_index'] = data['low'].rolling(window=20).apply(lambda x: x.idxmin())
    data['group'] = (data['low_index'] != data['low_index'].shift()).cumsum()
    data['days_since_low'] = data.groupby('group').cumcount() + 1
    data[f'low_lag_{windows}']=data[f'low_{windows}'].shift()
    data['days_since_low_lag']=data['days_since_low'].shift()
    
    return data

def get_day_high(data,windows):
    data[f'high_{windows}']=data['high'].rolling(window=windows).max()
    data['high_index'] = data['high'].rolling(window=20).apply(lambda x: x.idxmax())
    data['group'] = (data['high_index'] != data['high_index'].shift()).cumsum()
    data['days_since_high'] = data.groupby('group').cumcount() + 1
    data[f'high_lag_{windows}']=data[f'high_{windows}'].shift()
    data['days_since_high_lag']=data['days_since_high'].shift()
    return data

def find_signal(close,low_20d,high_20d,days_since_low,days_since_high,low,high):
        if days_since_low>3 and close<=low_20d and low<low_20d:
            return 'buy'
        elif days_since_high>3 and close>=high_20d and high>high_20d:
            return 'sell'

def calculate_sl_tp(open_price, atr, signal):
    if signal == 'buy':
        sl = open_price - 2 * atr
        tp = open_price + 3 * atr
        # if (tp-open_price)/open_price>0.002:
        #     tp=open_price+open_price*0.002
    elif signal == 'sell':
        sl = open_price + 2 * atr
        tp = open_price - 3 * atr
    return sl, tp

def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=30
    return data

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
        

    def close_position(self,close_date_time,close_price,status):
        self.close_datetime=close_date_time
        self.close_price=close_price
        if 'JPY' in self.symbol:
            self.profit=(self.close_price-self.open_price)*self.volume*0.0094 if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume*0.0094
        else:
            self.profit=(self.close_price-self.open_price)*self.volume if self.order_type=='buy' else (self.open_price-self.close_price)*self.volume
        self.status=status
   
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
        i=0
        for pos in self.positions:
            if pos.status=='open':
                i=i+1
        if  i>=2:
            return False
        else:
            return True
    
    def run(self,trade):
        
        is_trade=0
        trade_signal=None
        threshold_buy=None
        threshold_sell=None
        track_order=0
        
        for i, data in self.data.iterrows():  
            

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
                        if (is_trade==0 or is_trade==1.2) and data.signal=='buy' and track_order<=1:
                            # print(f'123-{data.time}')
                            is_trade=1.0
                            trade_signal='buy'
                            threshold_buy=data[f'low_lag_{window}']
                        elif (is_trade==0 or is_trade==2.2) and data.signal=='sell' and track_order<=1:
                            is_trade=2.0
                            trade_signal='sell'
                            threshold_sell=data[f'high_lag_{window}']
                        
                    
                    if trade==True:
                        
                        if (is_trade==1.0 or is_trade==1.2) and self.trading_allowed() :
                          if next_row.high>threshold_buy:
                              is_trade=1.1
                          else: is_trade=1.2
                          
                        elif is_trade==1.1 and self.trading_allowed():
                            order_price=data.close
                            if next_row.low<=order_price:
                                # print(f'456-{data.time}')
                                sl,tp=calculate_sl_tp(order_price, data.atr,trade_signal)
                                self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade))
                                track_order=track_order+1
                                is_trade=0
                                threshold_buy=None
                            else: 
                                is_trade=0
                                threshold_buy=None
                                
                        elif (is_trade==2.0 or is_trade==2.2) and self.trading_allowed():
                        #   print(data.time)
                        #   print(threshold_sell)
                        #   print(next_row.low)
                          if next_row.low<=threshold_sell:
                              is_trade=2.1
                          else: is_trade=2.2
                          
                        elif is_trade==2.1 and self.trading_allowed():
                            order_price=data.close
                            if next_row.high>=order_price:
                                # print(f'456-{data.time}')
                                sl,tp=calculate_sl_tp(order_price, data.atr,trade_signal)
                                self.add_position(position(next_row.time,order_price,trade_signal,self.volume,sl,tp,currency,is_trade))
                                is_trade=0
                                threshold_sell=None
                            else: 
                                is_trade=0
                                threshold_sell=None
                        for pos in self.positions:
                            
                            if pos.status=='open' and data.time>=pos.open_datetime:
                                
                                df123=self.get_positions_df()
                                if not df123.empty:
                                    profit= df123['pnl_close'].iloc[-1]
                                if pos.order_type=='buy':
                                    if 'JPY' in currency:
                                        total_profit=(data.low-pos.open_price)*pos.volume*0.0094+profit
                                    else:
                                        total_profit=(data.low-pos.open_price)*pos.volume+profit
                                elif pos.order_type=='sell':
                                    if 'JPY' in currency:  
                                        total_profit=(pos.open_price-data.high)*pos.volume*0.0094+profit
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
                                elif pos.order_type=='sell' and data.signal=='buy' :
                                    pos.close_position(next_row.time,data.close,'closed')
                                    track_order=track_order-1 
                                elif pos.order_type=='buy' and data.signal=='sell' :
                                    pos.close_position(next_row.time,data.close,'closed')
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
years=list(range(2018, 2024 + 1, 1))
# symbol=['GBPNZD','GBPCAD','NZDCAD','GBPAUD','GBPUSD']

symbol=['USDCAD']
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
        bars=mt.copy_rates_range(currency,mt.TIMEFRAME_D1,datetime(year,1,1), datetime(year,12,31))
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
        
        window=20
        df=get_day_low(df,window)
        df=get_day_high(df,window)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df.dropna(subset=[f'low_lag_{window}'], inplace=True)
        df['signal']=np.vectorize(find_signal)(df['close'],df[f'low_lag_{window}'],df[f'high_lag_{window}'],df['days_since_low_lag'],df['days_since_high_lag'],df['low'],df['high'])
        df.reset_index(inplace=True)


        # df.to_csv(f'E:/EA/bollinger-bands/H4_year/b_{year}_opi_8.5.csv')
        df.to_csv(f'C:/c/EA/Turtle Soup/D1/b_{year}_opi_1.0.csv')
        print(f'{currency} have been got and start run the strategy')
        for volume in volumes:
            print(volume)
            bollinger_strategy=Strategy(df,200,volume)
            trade=True
            result=bollinger_strategy.run(trade)
            open_rows = result
            if not open_rows.empty:
                print(open_rows)
            last=result[-1:]
            df1=pd.concat([df1,result])
            df2=pd.concat([df2,last])
            j=j+1
            print(f'{currency} have finished-{j}')
        df=df.merge(df1,how='left',left_on=['time'],right_on=['open_datetime'])
        df.to_csv(f'C:/c/EA/Turtle Soup/D1/b_{year}_opi_result_1.0.csv',index=False)
        # df.to_csv(f'E:/EA/bollinger-bands/H4_year/b_{year}_opi_result_8.5.csv',index=False)

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
    
df1.to_csv(f'C:/c/EA/Turtle Soup/D1/result_detail_volumn_rsi_opi_1.0.csv')
df2.to_csv(f'C:/c/EA/Turtle Soup/D1/final_result_volumn_detail_rsi_opi_1.0.csv')
# df1.to_csv(f'E:/EA/bollinger-bands/H4_year/result_detail_volumn_rsi_opiti_8.5.csv')
# df2.to_csv(f'E:/EA/bollinger-bands/H4_year/final_result_volumn_detail_opiti_8.5.csv')
# 'E:/EA/bollinger-bands/H1_year'
print('finish')
