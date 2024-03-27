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


import pandas as pd

# Sample DataFrame with 'date' and 'close_price' columns
# Replace this with your actual DataFrame
data = {'date': pd.date_range(start='2023-01-01', end='2023-12-31', freq='D'),
        'close_price': [100, 105, 110, 108, 112, 115, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 160, 156, 152, 148, 144, 140, 136, 132, 128, 124, 120, 116, 112, 108, 104, 100]}
df = pd.DataFrame(data)

def find_high_low_points(df, window_size):
    high_points = []
    low_points = []
    high_price = -float('inf')  # Initialize to negative infinity
    low_price = float('inf')    # Initialize to positive infinity
    
    for i in range(len(df)):
        if i >= window_size:  # Start checking from the window_size index
            window_prices = df['close_price'].iloc[i-window_size:i]  # Get prices within the window
            max_price = window_prices.max()
            min_price = window_prices.min()
            
            if df['close_price'].iloc[i] == max_price and max_price > high_price:
                high_price = max_price
                high_points.append((df.index[i], high_price))
            elif df['close_price'].iloc[i] == min_price and min_price < low_price:
                low_price = min_price
                low_points.append((df.index[i], low_price))
                
    return high_points, low_points

# Specify the window size for finding high and low points
window_size = 5  # Adjust as needed

high_points, low_points = find_high_low_points(df, window_size)

print("High Points:")
for point in high_points:
    print("Date:", point[0], "| High Price:", point[1])

print("\nLow Points:")
for point in low_points:
    print("Date:", point[0], "| Low Price:", point[1])
