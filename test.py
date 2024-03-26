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
df.set_index('time', inplace=True)

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