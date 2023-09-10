import json
import oandapyV20
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.accounts import AccountList,AccountInstruments
from oandapyV20.endpoints.instruments import InstrumentsCandles
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.pricing as PricingInfo
from oandapyV20.definitions.instruments import CandlestickGranularity
import pandas as pd
import pytz
import numpy as np

# Replace 'YOUR_API_KEY' with your actual OANDA API key
api_key = '2b01bb194c3e8913fb32a009e1708a06-971c216690feb7f9c027b794773dc9e2'

# Set up the API connection
api = API(access_token=api_key, environment='practice')
print(api)

r = AccountList()
response = api.request(r)

# Process the account information
if 'accounts' in response:
        accounts = response['accounts']
        for account in accounts:
            account_id = account['id']
            print(account_id)
else:
        print('Unable to retrieve account information.')


params = {
    "from": "2020-01-01",     # Specify the start date
    "to": "2023-07-18",       # Specify the end date
    "granularity": "D",       # Specify the granularity (D = Daily)
        }


endpoint = InstrumentsCandles(
        instrument="AUD_USD",
        params=params
    )
response = api.request(endpoint)

# Process the historical data
if 'candles' in response:
        candles = response['candles']
        df = pd.DataFrame(columns=['Timestamp', 'Open', 'High', 'Low', 'Close'])
        for candle in candles:
            timestamp = candle['time']
            open_price = candle['mid']['o']
            high_price = candle['mid']['h']
            low_price = candle['mid']['l']
            close_price = candle['mid']['c']
            df = df._append({'Timestamp': timestamp, 'Open': open_price, 'High': high_price, 'Low': low_price, 'Close': close_price}, ignore_index=True)
else:
        print('Unable to retrieve historical data.')

df['date_time'] = pd.to_datetime(df['Timestamp'])
sydney_tz = pytz.timezone('Australia/Sydney')
df['date_time_sydney'] = df['date_time'].dt.tz_convert(sydney_tz)
df['sydney_date'] = df['date_time_sydney'].dt.date
df['100-day SMA'] = df['Close'].rolling(window=100).mean()
df['200-day SMA'] = df['Close'].rolling(window=200).mean()

df['cross']=np.where(df['100-day SMA'].isnull() | df['200-day SMA'].isnull(), "Null",
                    np.where((df['100-day SMA']>df['200-day SMA']), '100-day>200-day','100-day<=200-day'))
df['cross(pre)']=df['cross'].shift(1)

df['key_point']=np.where(df['cross']==df['cross(pre)'], "Null","Yes")

df['triger_cross']=np.where(df['100-day SMA'].isnull() | df['200-day SMA'].isnull(), "Null",
                            np.where(df['Close'].astype(float)>df['100-day SMA'], 'Close>100-day','Close<=100-day'))
df['triger_cross(pre)']=df['triger_cross'].shift(1)

df['trigger_point']=np.where(df['triger_cross']==df['triger_cross(pre)'], "Null",
                            np.where(df['triger_cross']=='Close>100-day',"buy_trigger","sell_trigger"))

df['confirm_cross']=np.where(df['100-day SMA'].isnull() | df['200-day SMA'].isnull(), "Null",
                            np.where(df['Close'].astype(float)>df['200-day SMA'], 'Close>200-day','Close<=200-day'))
df['confirm_cross(pre)']=df['confirm_cross'].shift(1)

df['confirm_point']=np.where(df['confirm_cross']==df['confirm_cross(pre)'], "Null",
                            np.where(df['confirm_cross']=='Close>200-day',"buy_confirm","sell_confirm"))


print(df)



print(df)
print(df)

crossing_points = df[df['50-day SMA'] > df['200-day SMA']].loc[:, ['sydney_date', '50-day SMA', '200-day SMA']]

print(crossing_points)

print(df)
df.to_csv('E:/EA/AUD_USD.csv')
print(df)



# Specify the currency pairs to subscribe to
currency_pairs = ["AUD_USD"]

try:
    # Create the pricing stream request
    params = {
        "instruments": ','.join(currency_pairs)
    }
    print(params)
    r = pricing.PricingStream(accountID='101-011-26256631-001', params=params)
    print(r)
    # Start the streaming data
    rv=api.request(r)
    maxrecs = 10
    for tick in rv:
        print(json.dumps(tick, indent=4))
        maxrecs -= 1
        if maxrecs == 0:
            r.terminate("maxrecs records received")
        if tick['type'] == 'PRICE':
            instrument = tick['instrument']
            time = tick['time']
            bid_price = tick['bids'][0]['price']
            ask_price = tick['asks'][0]['price']
            print(f"Instrument: {instrument}, Time: {time}, Bid: {bid_price}, Ask: {ask_price}")

except V20Error as e:
    print(f"Error: {e}")





instrument = "BTC_USD"

try:
    # Create the instrument candles request
    params = {
        "count": 1
    }
    r = InstrumentsCandles(instrument="BTC_USD",params=params)

    # Fetch the instrument candles
    response = api.request(r)

    print(response)

    # Extract the index price from the response
    index_price = response['candles'][0]['mid']['c']
    print(f"Index Price for {instrument}: {index_price}")

except V20Error as e:
    print(f"Error: {e}")


try:
    # Create the account instruments request
    r = AccountInstruments(accountID='101-011-26256631-001')

    # Fetch the account instruments
    response = api.request(r)

    # Extract the currency names from the response
    currency_names = [instrument['name'] for instrument in response['instruments']]
    print("Currency Names:")
    for currency_name in currency_names:
        print(currency_name)

except V20Error as e:
    print(f"Error: {e}")












# Replace 'YOUR_ACCOUNT_ID' with your actual OANDA account ID
account_id = '101-011-26256631-001'

# Specify the currency pair and time range for historical data
currency_pair = 'EUR_USD'  # Example: Euro to US Dollar
start_date = '2022-01-01'  # Example: Start date for historical data
end_date = '2022-01-31'    # Example: End date for historical data

# Construct the API URL
url = f'https://api-fxtrade.oanda.com/v3/accounts'

# Send the HTTP GET request with required headers
headers = {
    'Authorization': f'Bearer {api_key}',
    # 'Accept-Datetime-Format': 'UNIX',
}
response = requests.get(url, headers=headers)

# Parse the JSON response
data = json.loads(response.text)

print(data)
