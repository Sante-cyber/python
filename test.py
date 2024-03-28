import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import talib
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks
from common import login,password,server
import MetaTrader5 as mt
from datetime import datetime,timedelta
login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)
currency='GBPAUD'
year=2023
bars=mt.copy_rates_range(currency,mt.TIMEFRAME_H4,datetime(year,1,1), datetime(year,12,31))

df = pd.DataFrame(bars)
df['time']=pd.to_datetime(df['time'],unit='s')
# df.set_index('time', inplace=True)

def identify_swings(prices, window=5):
    low_points = []
    
    for i in range(window, len(prices) - window):
        window_prices = prices[i - window:i + window + 1]
        min_index = np.argmin(window_prices)
        
        if min_index == window:
            low_points.append(i)
    
    return low_points

# Function to calculate lower trendline
def calculate_lower_trendline(prices, low_points):
    # Extract x (time) and y (price) values for low points
    x = np.arange(len(prices))
    y = prices.values

    # Fit linear regression model to low points
    lr = LinearRegression()
    lr.fit(x[low_points].reshape(-1, 1), y[low_points])

    # Predict prices using the linear model
    trendline_low = lr.predict(x.reshape(-1, 1))

    return trendline_low

# Identify swing low points
low_points = identify_swings(df['close'])

# Calculate lower trendline
trendline_low = calculate_lower_trendline(df['close'], low_points)

print(trendline_low)

def find_lower_high_point(df):
    for i in range(1, len(df) - 1):
        if df['close'][i] > df['close'][i - 1] and df['close'][i] > df['close'][i + 1]:
            df.at[i, 'high_point'] = 1
        elif df['close'][i] < df['close'][i - 1] and df['close'][i] < df['close'][i + 1]:
            df.at[i, 'low_point'] = 1
    
    return(df)



# Function to find the closest high point price and index before the given price
def find_closest_high_point(price, index):
    closest_high_point = df[(df['high_point'] == 1) & (df.index < index)]
    if not closest_high_point.empty:
        closest_high_point = closest_high_point.iloc[-1]
        return closest_high_point['close'], closest_high_point.name
    else:
        return None, None

# Function to find the closest low point price and index before the given price
def find_closest_low_point(price, index):
    closest_low_point = df[(df['low_point'] == 1) & (df.index < index)]
    if not closest_low_point.empty:
        closest_low_point = closest_low_point.iloc[-1]
        return closest_low_point['close'], closest_low_point.name
    else:
        return None, None

# Add new columns for previous high point price, index, previous low point price, and index
df['previous_high_point'], df['previous_high_point_index'] = zip(*df.apply(lambda row: find_closest_high_point(row['close'], row.name), axis=1))
df['previous_low_point'], df['previous_low_point_index'] = zip(*df.apply(lambda row: find_closest_low_point(row['close'], row.name), axis=1))

df.to_csv('C:/Ally/a.csv')