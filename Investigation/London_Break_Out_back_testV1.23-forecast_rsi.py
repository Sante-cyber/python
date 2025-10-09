import pandas as pd
import numpy as np
from datetime import datetime
import MetaTrader5 as mt
import pandas_ta as ta
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE

# Initialize and login to MetaTrader 5
login = 51658107
password = 'VxBvOa*4'
server = 'ICMarkets-Demo'
mt.initialize()
mt.login(login, password, server)

# Fetch historical data
symbol = 'EURJPY'
bars = mt.copy_rates_range(symbol, mt.TIMEFRAME_M30, datetime(2020, 1, 1), datetime(2020, 12, 31))
df = pd.DataFrame(bars)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculate technical indicators
df['rsi'] = ta.rsi(df['close'], length=14)
df['ma'] = df['close'].rolling(window=14).mean()
df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
df['bollinger_upper'] = ta.bbands(df['close'],length=20,std=2.0)['BBU_20_2.0']
df['bollinger_lower'] = ta.bbands(df['close'],length=20,std=2.0)['BBL_20_2.0']

# Create lag features
df['rsi_lag1'] = df['rsi'].shift(1)
df['rsi_lag2'] = df['rsi'].shift(2)
df['ma_lag1'] = df['ma'].shift(1)
df['macd_lag1'] = df['macd'].shift(1)
df['bollinger_upper_lag1'] = df['bollinger_upper'].shift(1)
df['bollinger_lower_lag1'] = df['bollinger_lower'].shift(1)

# Create time-based features
df['hour'] = df['time'].dt.hour
df['day_of_week'] = df['time'].dt.dayofweek

# Create the target variable
df['target_rsi'] = df['rsi'].shift(-1)
df['target'] = (df['target_rsi'] > 70).astype(int)

# Drop NaN values
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)

# Define features and target
features = [
    'rsi_lag1', 'rsi_lag2', 'ma_lag1', 'macd_lag1', 
    'bollinger_upper_lag1', 
    'bollinger_lower_lag1', 'hour', 'day_of_week'
]
target = 'target'

# Split the data into training and testing sets
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

X_test_index = X_test.index

# Handle class imbalance
smote = SMOTE()
X_train, y_train = smote.fit_resample(X_train, y_train)

# Standardize features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train a Random Forest model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Predict the target values
y_pred = model.predict(X_test)

# Evaluate the model
print(classification_report(y_test, y_pred))

# Hyperparameter tuning
param_grid = {
    'n_estimators': [300],
    'max_depth': [20],
    'min_samples_split': [2]
}
grid_search = GridSearchCV(RandomForestClassifier(), param_grid, cv=5, scoring='recall')
grid_search.fit(X_train, y_train)

# Best parameters
print('Best parameters found: ', grid_search.best_params_)
best_model = grid_search.best_estimator_

# Evaluate the best model
y_pred_best = best_model.predict(X_test)
print(classification_report(y_test, y_pred_best))


df_test = df.iloc[X_test_index]
df_test['predicted_target'] = y_pred
df_test.to_csv('C:/Ally/a.csv')